# python realtime.py --source 0 --log face_tracking.log --interval 10
# python realtime_log.py --source 0 --log surveillance.log --interval 20

import argparse
import pickle
import time
import cv2
import numpy as np
import logging
from datetime import datetime
from ultralytics import YOLO
from insightface.app import FaceAnalysis

# Cosine similarity threshold (0.4 - 0.5 is usually optimal for buffalo_l)
SIMILARITY_THRESHOLD = 0.45

def setup_logger(log_file_path: str):
    """Initializes a continuous file logger."""
    logger = logging.getLogger("FaceTracker")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # File handler to continuously append logs
        file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Also print log updates directly to terminal console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

def load_face_db(pkl_path: str):
    with open(pkl_path, "rb") as f:
        return pickle.load(f)

def match_face(embedding, face_db):
    """Compares an embedding against the database using cosine similarity."""
    best_name = "Unknown"
    best_score = -1.0

    for name, ref_embeddings in face_db.items():
        for ref_emb in ref_embeddings:
            score = np.dot(embedding, ref_emb)
            if score > best_score:
                best_score = score
                best_name = name

    if best_score >= SIMILARITY_THRESHOLD:
        return f"{best_name} ({best_score:.2f})"
    return "Unknown"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=str, default="../database/face_db.pkl", help="Path to enrolled face database pkl")
    parser.add_argument("--model", type=str, default="yolo26n.pt", help="Path to YOLO26 model")
    parser.add_argument("--source", type=str, default="0", help="Camera index (0) or path to video file")
    parser.add_argument("--log", type=str, default="../database/face_tracking.log", help="Output file path for tracking logs")
    parser.add_argument("--interval", type=int, default=10, help="Log interval in seconds for each active track")
    args = parser.parse_args()

    # 0. Setup continuous logging
    logger = setup_logger(args.log)
    logger.info("Initializing surveillance tracking system...")

    # 1. Load enrolled face database
    logger.info(f"Loading face database from {args.db}...")
    face_db = load_face_db(args.db)

    # 2. Initialize YOLO26 and ByteTrack
    logger.info(f"Initializing YOLO26 model ({args.model})...")
    yolo_model = YOLO(args.model)

    # 3. Initialize InsightFace for runtime recognition
    logger.info("Initializing InsightFace (buffalo_l)...")
    face_app = FaceAnalysis(name="buffalo_l")
    face_app.prepare(ctx_id=0, det_size=(320, 320)) 

    # Track identities recognized across frame sequences
    identity_cache = {}
    
    # Track the last epoch timestamp a logging update was written for a given track_id
    # track_id -> float (timestamp)
    last_logged_time = {}

    # Open Camera Stream
    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source, cv2.CAP_V4L2)

    logger.info(f"Starting video stream. Logging updates every {args.interval} seconds. Press 'q' to exit.")
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Run YOLO26 + ByteTrack tracking (filtering for class 0: person)
        results = yolo_model.track(frame, tracker="bytetrack.yaml", persist=True, classes=[0], verbose=False)
        
        # Check if objects are actively being tracked
        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().tolist()

            current_time = time.time()

            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = map(int, box)
                
                # If this person hasn't been recognized yet, extract their face
                if track_id not in identity_cache:
                    h, w, _ = frame.shape
                    crop_x1, crop_y1 = max(0, x1), max(0, y1)
                    crop_x2, crop_y2 = min(w, x2), min(h, y2)
                    person_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]

                    if person_crop.size > 0:
                        faces = face_app.get(person_crop)
                        if faces:
                            face = max(faces, key=lambda f: (f.bbox - f.bbox) * (f.bbox - f.bbox))
                            identity = match_face(face.normed_embedding, face_db)
                            identity_cache[track_id] = identity
                        else:
                            identity_cache[track_id] = "Unknown"
                    else:
                        identity_cache[track_id] = "Unknown"
                
                # INTERVAL LOGGING GATE: Log if it is the first time seeing them OR if the interval has passed
                if track_id not in last_logged_time or (current_time - last_logged_time[track_id] >= args.interval):
                    log_msg = f"[TRACK UPDATE] Tracking ID: {int(track_id)} | Identity: {identity_cache[track_id]}"
                    logger.info(log_msg)
                    # Update the baseline timestamp for this track
                    last_logged_time[track_id] = current_time

                # Retrieve the cached identity for this persistent track ID
                label_text = f"ID {int(track_id)}: {identity_cache[track_id]}"

                # Draw tracking box and identity overlay
                color = (0, 255, 0) if "Unknown" not in identity_cache[track_id] else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Display output feed
        cv2.imshow("YOLO26 + ByteTrack + InsightFace Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    logger.info("Video stream closed by user. Exiting pipeline.")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
