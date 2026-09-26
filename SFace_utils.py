import os
import glob
import cv2
import numpy as np

def initialize_model(detector_model_path, recognizer_model_path, input_size=(0, 0), score_threshold=0.45, nms_threshold=0.3):
    # 1. Initialize OpenCV YuNet Detector and SFace Recognizer
    #detector = cv2.FaceDetectorYN.create("Datasets/face_detection_yunet_2023mar.onnx", "", (0, 0))
    detector = cv2.FaceDetectorYN.create(
        model=detector_model_path,
        config="",
        input_size=input_size,
        score_threshold=score_threshold,   # <-- Drop from 0.9 to 0.45 to catch blurry faces
        nms_threshold=nms_threshold
    )

    recognizer = cv2.FaceRecognizerSF.create(recognizer_model_path, "")

    return detector, recognizer

def extract_embedding(img_path):
    """Loads an image (handles high-res downscaling) and extracts SFace embedding."""
    img = cv2.imread(img_path)
    if img is None:
        return None
    
    h_orig, w_orig, _ = img.shape
    target_width = 1000
    
    # Safely downscale high-res images (e.g., 4032x3024) for YuNet detection
    if w_orig > target_width:
        scale_factor = target_width / float(w_orig)
        img_small = cv2.resize(img, (target_width, int(h_orig * scale_factor)))
        detector.setInputSize((img_small.shape[1], img_small.shape[0]))
        _, faces = detector.detect(img_small)
        if faces is not None:
            faces[:, :14] = faces[:, :14] / scale_factor
    else:
        detector.setInputSize((w_orig, h_orig))
        _, faces = detector.detect(img)

    if faces is None:
        return None

    face_aligned = recognizer.alignCrop(img, faces)
    return recognizer.feature(face_aligned)

# 2. Load Folder Structure into Memory
def load_face_templates(dataset_dir):
    """
    Scans folders, averages embeddings for people with multiple photos,
    and returns a dictionary: { "Person_Name": embedding_array }
    """
    templates = {}
    valid_extensions = ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.JPG', '*.JPEG', '*.PNG')
    
    if not os.path.exists(dataset_dir):
        print(f"Error: Directory '{dataset_dir}' not found.")
        return templates

    print(f"Indexing dataset folder: {dataset_dir}")
    
    for person_name in os.listdir(dataset_dir):
        person_folder = os.path.join(dataset_dir, person_name)
        if not os.path.isdir(person_folder):
            continue
            
        image_paths = []
        for ext in valid_extensions:
            image_paths.extend(glob.glob(os.path.join(person_folder, ext)))
            
        if not image_paths:
            continue
            
        person_embeddings = []
        for img_path in image_paths:
            embedding = extract_embedding(img_path)
            if embedding is not None:
                person_embeddings.append(embedding)
                
        if person_embeddings:
            # Average vectors for robust multi-photo templates
            master_embedding = np.mean(person_embeddings, axis=0, dtype=np.float32)
            cv2.normalize(master_embedding, master_embedding)
            templates[person_name] = master_embedding
            print(f" -> Indexed: {person_name} ({len(person_embeddings)} photos)")
            
    print("--- Indexing Complete ---\n")
    return templates

# 3. Match a Query Image Against Loaded Templates
def identify_face_from_memory(query_img_path, templates):
    """Compares a new face image against the dictionary of loaded templates."""
    query_feat = extract_embedding(query_img_path)
    if query_feat is None:
        print("Could not detect a face in the query image.")
        return "Unknown"

    best_match_name = "Unknown"
    highest_score = -1.0
    SFACE_THRESHOLD = 0.363 # Official OpenCV Cosine Threshold

    # Loop through our dictionary keys and vector arrays
    for person_name, db_feat in templates.items():
        score = recognizer.match(query_feat, db_feat, cv2.FaceRecognizerSF_FR_COSINE)
        
        if score > highest_score:
            highest_score = score
            if score >= SFACE_THRESHOLD:
                best_match_name = person_name

    print(f"Result: Match found -> {best_match_name} (Score: {highest_score:.4f})")
    return best_match_name


def extract_all_faces(image_path, detector_model_path, recognizer_model_path, output_folder, score_threshold=0.5):
    # 1. Initialize OpenCV Zoo models
    # detector = cv2.FaceDetectorYN.create("Datasets/face_detection_yunet_2023mar.onnx", "", (0, 0), score_threshold=0.5)
    detector = cv2.FaceDetectorYN.create(detector_model_path, "", (0, 0), score_threshold=score_threshold)
    # recognizer = cv2.FaceRecognizerSF.create("Datasets/face_recognition_sface_2021dec.onnx", "")
    recognizer = cv2.FaceRecognizerSF.create(recognizer_model_path, "")

    # Create destination folder if missing
    os.makedirs(output_folder, exist_ok=True)

    # 2. Load the input image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Unable to load target image at '{image_path}'")
        return

    h_orig, w_orig, _ = img.shape
    target_width = 1000

    # 3. Downscale dynamic dimensions for YuNet if image is massive (e.g. 4032x3024)
    if w_orig > target_width:
        scale_factor = target_width / float(w_orig)
        img_small = cv2.resize(img, (target_width, int(h_orig * scale_factor)))
        detector.setInputSize((img_small.shape[1], img_small.shape[0]))
        _, faces = detector.detect(img_small)
        if faces is not None:
            # Scale coordinates back to original size dimensions
            faces[:, :14] = faces[:, :14] / scale_factor
    else:
        detector.setInputSize((w_orig, h_orig))
        _, faces = detector.detect(img)

    # 4. Process and save each face found
    if faces is None or len(faces) == 0:
        print("No faces detected in the image.")
        return

    print(f"Detected {len(faces)} face(s). Extracting clean crops...")

    for idx, face in enumerate(faces):
        # Format the face parameters into a 2D numpy matrix row structure
        single_face_input = np.array([face])
        
        try:
            # SFace extracts a perfectly aligned and cropped 112x112 portrait 
            face_aligned = recognizer.alignCrop(img, single_face_input)
            
            # Save the cropped face profile to disk
            output_filename = os.path.join(output_folder, f"face_{idx + 1}.png")
            cv2.imwrite(output_filename, face_aligned)
            print(f" -> Saved: {output_filename}")
        except Exception as e:
            print(f" -> Failed to extract face index {idx + 1}: {e}")

    print(f"\nFinished! Check the '{output_folder}' directory for your images.")

