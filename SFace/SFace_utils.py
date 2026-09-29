import os
import glob
import cv2
import numpy as np
from pathlib import Path

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

def extract_embedding(img_path, detector, recognizer):
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
def load_face_templates(detector_model, recognizer_model, dataset_dir):
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
            embedding = extract_embedding(img_path=img_path, detector=detector_model, recognizer=recognizer_model)
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
def identify_face_from_memory(detector_model, recognizer_model, query_img_path, templates):
    """Compares a new face image against the dictionary of loaded templates."""
    query_feat = extract_embedding(query_img_path, detector=detector_model, recognizer=recognizer_model)
    if query_feat is None:
        print("Could not detect a face in the query image.")
        return "Unknown"

    best_match_name = "Unknown"
    highest_score = -1.0
    SFACE_THRESHOLD = 0.363 # Official OpenCV Cosine Threshold

    # Loop through our dictionary keys and vector arrays
    for person_name, db_feat in templates.items():
        score = recognizer_model.match(query_feat, db_feat, cv2.FaceRecognizerSF_FR_COSINE)
        
        if score > highest_score:
            highest_score = score
            if score >= SFACE_THRESHOLD:
                best_match_name = person_name

    print(f"Result: Match found -> {best_match_name} (Score: {highest_score:.4f}): {query_img_path}")
    return best_match_name


def extract_all_faces(image_path=False, detector_model=False, recognizer_model=False, output_folder=False, 
                      score_threshold=0.5, file_count=0, file_name=False):
    # 1. Initialize OpenCV Zoo models
    # detector = cv2.FaceDetectorYN.create("Datasets/face_detection_yunet_2023mar.onnx", "", (0, 0), score_threshold=0.5)
    # detector = cv2.FaceDetectorYN.create(detector_model_path, "", (0, 0), score_threshold=score_threshold)
    # detector = detector_model
    # recognizer = cv2.FaceRecognizerSF.create("Datasets/face_recognition_sface_2021dec.onnx", "")
    # recognizer = cv2.FaceRecognizerSF.create(recognizer_model_path, "")
    # recognizer = recognizer_model

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
        detector_model.setInputSize((img_small.shape[1], img_small.shape[0]))
        _, faces = detector_model.detect(img_small)
        if faces is not None:
            # Scale coordinates back to original size dimensions
            faces[:, :14] = faces[:, :14] / scale_factor
    else:
        detector_model.setInputSize((w_orig, h_orig))
        _, faces = detector_model.detect(img)

    # 4. Process and save each face found
    if faces is None or len(faces) == 0:
        print("No faces detected in the image.")
        return

    print(f"Detected {len(faces)} face(s). Extracting clean crops...")

    for idx, face in enumerate(faces):
        # Format the face parameters into a 2D numpy matrix row structure
        single_face_input = np.array([face])
        
        try:
            file_count +=1 
            # SFace extracts a perfectly aligned and cropped 112x112 portrait 
            face_aligned = recognizer_model.alignCrop(img, single_face_input)
            
            # Save the cropped face profile to disk
            # output_filename = os.path.join(output_folder, f"face_{idx + 1}.jpg")
            if file_name:
                output_filename = os.path.join(output_folder, f"{file_name}.jpg")
            else:
                output_filename = os.path.join(output_folder, f"face_{file_count}.jpg")

            cv2.imwrite(output_filename, face_aligned)
            print(f" -> Saved: {output_filename}")
        except Exception as e:
            print(f" -> Failed to extract face index {idx + 1}: {e}")

    print(f"\nFinished! Check the '{output_folder}' directory for your images.")

    return file_count

def files_from_folder(dataset_path = False):    
    # The '**/*.jpg' means look through ALL subfolders for any .jpg file
    subfolder_pattern = os.path.join(dataset_path, "**", "*.jpg")
    all_subfolder_images = glob.glob(subfolder_pattern, recursive=True)

    print(f"Found {len(all_subfolder_images)} images across all subfolders.")
    for file_path in all_subfolder_images:
        print(file_path)

    return all_subfolder_images

def ideentify_faces(detector_model, recognizer_model, face_database_dict, images_list):
    for idx in images_list:
        # identify_face_from_memory("Datasets/"+idx, face_database_dict)
        identify_face_from_memory(detector_model=detector_model, recognizer_model=recognizer_model, 
                            query_img_path=idx, templates=face_database_dict)


def get_folder_list(main_dir=False):
    ROOT_DIR = Path(main_dir)

    folder_list = sorted([
        folder.name
        for folder in ROOT_DIR.iterdir()
        if folder.is_dir()
    ])

    # print(folder_list)

    return folder_list

def prepare_sface_dataset(score_threshold=0.3, raw_dataset_dir=False, recognizer_model=False, detector_model=False, 
                          output_folder=False, dataset_dir=False):

    # Prepare SFace datset

    # get persons list
    perosns_list = get_folder_list(main_dir=raw_dataset_dir)

    # Extract all facses for SFace dataset
    for person in perosns_list:
            
            # get images file list of a person in raw data 
            print(Path(raw_dataset_dir) / person)
            person_images = files_from_folder(dataset_path=Path(raw_dataset_dir) / person)
            # print(person_images)

            # Person folder path
            person_dir = Path(dataset_dir) / person
            # print(person_dir)
            folder_path = Path(person_dir)

            # Create folder if it does not exist
            folder_path.mkdir(exist_ok=True)

            for img in person_images:
                    print(img)
                    file_name = img.split('/')[-1].replace('.jpg','')

                    # Extract face from image
                    extract_all_faces(image_path=img, recognizer_model=recognizer_model, detector_model=detector_model, 
                                    output_folder=person_dir, score_threshold=0.3, file_name=file_name)

    return True