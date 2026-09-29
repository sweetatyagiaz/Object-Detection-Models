import os
import glob
import cv2
import numpy as np
import csv
from datetime import datetime
import uuid

# ==========================================
# 1. CONFIGURATION & MODEL INITIALIZATION
# ==========================================
DATASET_DIR = "../database" # Working old dataset without face crop
DATASET_DIR = "../datasets/extracted_faces_datasets"
DETECTOR_MODEL = "../models/face_detection_yunet_2023mar.onnx"
RECOGNIZER_MODEL = "../models/face_recognition_sface_2021dec.onnx"

# Video matching threshold (slightly relaxed from 0.363 for real-world video noise)
VIDEO_SFACE_THRESHOLD = 0.33

# Working resolution for smooth edge inference
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ==========================================
# LOGGING CONFIGURATION
# ==========================================

CAMERA_ID = "CAM01"
# LOG_FILE = "face_recognition_log.csv"
# LOG_INTERVAL_SEC = 20

# logged_faces = {}
LOG_FILE = "face_tracking_log.csv"

LOG_INTERVAL_SEC = 10      # change to 20 if required
PERSON_TIMEOUT_SEC = 5

tracked_persons = {}


if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp",
            "Camera_ID",
            "Track_ID",
            "Person_ID",
            "Person_Name",
            "Score",
            "X",
            "Y",
            "W",
            "H",
            "Status"
        ])

# Initialize YuNet Face Detector with relaxed threshold for noisy/motion frames
detector = cv2.FaceDetectorYN.create(
    model=DETECTOR_MODEL,
    config="",
    input_size=(FRAME_WIDTH, FRAME_HEIGHT),
    score_threshold=0.5,   # Balanced between catching faces and avoiding false positives
    nms_threshold=0.3
)

# Initialize SFace Face Recognizer
recognizer = cv2.FaceRecognizerSF.create(
    model=RECOGNIZER_MODEL,
    config=""
)

# ==========================================
# 2. DATASET PARSING & TEMPLATE GENERATION
# ==========================================
def extract_embedding_from_file(img_path):
    """Loads an image, adjusts for scale, and extracts the 128D embedding."""
    img = cv2.imread(img_path)
    if img is None:
        return None
    
    h_orig, w_orig, _ = img.shape
    target_width = 1000
    
    # Scale down oversized files (e.g., 4K phone captures) for detection reliability
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

    # Align and extract feature vector
    face_aligned = recognizer.alignCrop(img, faces)
    return recognizer.feature(face_aligned)

def load_dataset_templates(dataset_path):
    """Parses subfolders and computes normalized master embeddings."""
    templates = {}
    valid_exts = ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.JPG', '*.JPEG', '*.PNG')
    
    if not os.path.exists(dataset_path):
        print(f"[-] Error: Directory '{dataset_path}' not found.")
        return templates

    print(f"[*] Indexing identities from '{dataset_path}'...")
    
    for person_name in sorted(os.listdir(dataset_path)):
        person_dir = os.path.join(dataset_path, person_name)
        if not os.path.isdir(person_dir):
            continue
            
        image_files = []
        for ext in valid_exts:
            image_files.extend(glob.glob(os.path.join(person_dir, ext)))
            
        if not image_files:
            print(f"    ! No valid photos for {person_name}. Skipping.")
            continue
            
        embeddings = []
        for img_file in image_files:
            emb = extract_embedding_from_file(img_file)
            if emb is not None:
                embeddings.append(emb)
                
        if embeddings:
            # Average multiple vectors to build a resilient representation
            master_vector = np.mean(embeddings, axis=0, dtype=np.float32)
            cv2.normalize(master_vector, master_vector)
            templates[person_name] = master_vector
            print(f"    -> Enrolled '{person_name}' ({len(embeddings)} image(s) processed)")
        else:
            print(f"    ! Warning: Failed to detect faces in all photos for '{person_name}'")
            
    print(f"[+] Indexing complete. {len(templates)} identities active in memory.\n")
    return templates

def log_event(track_id, person_id, person_name, score, box, status):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    x, y, w, h = box

    with open(
        LOG_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            timestamp,
            CAMERA_ID,
            track_id,
            person_id,
            person_name,
            round(float(score), 4),
            x,
            y,
            w,
            h,
            status
        ])

    print(
        f"[{status}] "
        f"{timestamp} | "
        f"ID={person_id} | "
        f"{person_name} | "
        f"{score:.4f}"
    )

# ==========================================
# 3. LIVE STREAM PROCESSING LOOP
# ==========================================
def run_live_recognition():
    # 1. Load identities from folders
    # templates = load_dataset_templates(DATASET_DIR)

    templates = load_dataset_templates(DATASET_DIR)

    person_ids = {
        name: idx
        for idx, name in enumerate(
            sorted(templates.keys()),
            start=1
        )
    }

    print("\nRegistered IDs")
    for name, pid in person_ids.items():
        print(f"{pid} -> {name}")
    print()

    if not templates:
        print("[-] No templates loaded. Please ensure dataset/ has images.")
        return

    # 2. Reset detector input size to the video dimensions
    detector.setInputSize((FRAME_WIDTH, FRAME_HEIGHT))

    # 3. Initialize Camera Stream (0 for default webcam, or replace with video filename/RTSP link)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print("[-] Error: Camera stream unavailable.")
        return

    print("[*] Starting live recognition. Press 'q' to exit.")
    
    frame_count = 0
    cached_detections = []  # Holds detection metadata to smooth out frame skipping

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[-] Stream ended or frame read error.")
            break

        # Ensure frame matches inference shape
        frame_resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        
        # Optimize system load: process detection and SFace every 2nd frame
        if frame_count % 2 == 0:
            cached_detections.clear()
            _, faces = detector.detect(frame_resized)

            if faces is not None:
                for face in faces:
                    # YuNet output layout: [0:4] bounding box, [4:14] landmarks, [14] score
                    single_face_input = np.array([face])
                    
                    try:
                        # Extract and match
                        aligned_crop = recognizer.alignCrop(frame_resized, single_face_input)
                        live_embedding = recognizer.feature(aligned_crop)

                        # best_name = "Unknown"
                        # max_score = -1.0

                        # for name, master_emb in templates.items():
                        #     similarity = recognizer.match(live_embedding, master_emb, cv2.FaceRecognizerSF_FR_COSINE)
                        #     if similarity > max_score:
                        #         max_score = similarity
                        #         if similarity >= VIDEO_SFACE_THRESHOLD:
                        #             best_name = name

                        best_name = "Unknown"
                        best_id = 0
                        max_score = -1.0

                        for name, master_emb in templates.items():

                            similarity = recognizer.match(
                                live_embedding,
                                master_emb,
                                cv2.FaceRecognizerSF_FR_COSINE
                            )

                            if similarity > max_score:

                                max_score = similarity

                                if similarity >= VIDEO_SFACE_THRESHOLD:
                                    best_name = name
                                    best_id = person_ids.get(name, 0)

                        # box = face[0:4].astype(int)
                        # cached_detections.append((box, best_name, max_score))
                        box = face[0:4].astype(int)

                        # if best_name != "Unknown":
                        #     log_recognition(
                        #         person_id=best_id,
                        #         person_name=best_name,
                        #         score=max_score
                        #     )
                        if best_name != "Unknown":
                            now = datetime.now()

                            if best_name not in tracked_persons:

                                track_id = str(uuid.uuid4())[:8]

                                tracked_persons[best_name] = {
                                    "track_id": track_id,
                                    "person_id": best_id,
                                    "last_seen": now,
                                    "last_logged": now,
                                    "best_score": max_score
                                }

                                log_event(
                                    track_id,
                                    best_id,
                                    best_name,
                                    max_score,
                                    box,
                                    "ENTER"
                                )

                            else:

                                tracked_persons[best_name]["last_seen"] = now

                                track_id = tracked_persons[best_name]["track_id"]

                                elapsed = (
                                    now -
                                    tracked_persons[best_name]["last_logged"]
                                ).total_seconds()

                                if elapsed >= LOG_INTERVAL_SEC:

                                    log_event(
                                        track_id,
                                        best_id,
                                        best_name,
                                        max_score,
                                        box,
                                        "PRESENT"
                                    )

                                    tracked_persons[best_name]["last_logged"] = now

                        cached_detections.append(
                            (
                                box,
                                best_name,
                                max_score
                            )
                        )
                    except Exception:
                        continue

        frame_count += 1

        # Render bounding boxes and identity labels
        for box, name, score in cached_detections:
            x, y, w, h = box
            is_recognized = (name != "Unknown")
            
            # Green for verified identity, red/amber for unknown
            color = (0, 255, 0) if is_recognized else (0, 0, 255)
            
            cv2.rectangle(frame_resized, (x, y), (x + w, y + h), color, 2)
            # label = f"{name} ({score:.2f})" if score > 0 else name
            if name != "Unknown":
                person_id = person_ids.get(name, 0)
                label = f"ID:{person_id} {name} ({score:.2f})"
            else:
                label = f"Unknown ({score:.2f})"
            cv2.putText(
                frame_resized, 
                label, 
                (x, max(20, y - 8)), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.55, 
                color, 
                2
            )

        now = datetime.now()

        remove_list = []

        for person_name, info in tracked_persons.items():

            elapsed = (
                now - info["last_seen"]
            ).total_seconds()

            if elapsed > PERSON_TIMEOUT_SEC:

                log_event(
                    info["track_id"],
                    info["person_id"],
                    person_name,
                    info["best_score"],
                    (0, 0, 0, 0),
                    "EXIT"
                )

                remove_list.append(person_name)

        for person_name in remove_list:
            del tracked_persons[person_name]
            
        cv2.imshow("SFace Live Recognition", frame_resized)

        # Press 'q' to gracefully shutdown
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[*] Pipeline shut down cleanly.")

if __name__ == "__main__":
    run_live_recognition()
