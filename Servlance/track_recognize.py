"""
track_recognize.py

Real-time pipeline: YOLO26 detection -> ByteTrack tracking (built into ultralytics)
-> local face recognition against an enrolled database (see enroll_faces.py).

Each person gets a stable track_id from ByteTrack. Recognition is only run every
N frames per track (not every frame) to save compute, and once a track is matched
with high confidence its label is cached for the rest of the track's life.

Usage:
    python track_recognize.py --source rtsp://camera_ip/stream --db face_db.pkl
    python track_recognize.py --source 0 --db face_db.pkl          # webcam test
    python track_recognize.py --source video.mp4 --db face_db.pkl --show
"""

import argparse
import pickle
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO
from insightface.app import FaceAnalysis

COCO_PERSON_CLASS_ID = 0
RECOGNITION_INTERVAL = 10       # re-check recognition every N frames per track
MATCH_THRESHOLD = 0.45          # cosine similarity threshold for a positive ID match
EMBEDDING_UNKNOWN_LABEL = "unknown"


class TrackState:
    """Per-track cache: avoids re-running face recognition every frame."""

    def __init__(self):
        self.label = None            # assigned identity, or "unknown"
        self.best_score = -1.0       # best similarity seen so far for this track
        self.frames_since_check = RECOGNITION_INTERVAL  # force a check on first sighting


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def match_face(embedding: np.ndarray, database: dict):
    """Return (best_name, best_score) against all enrolled embeddings."""
    best_name, best_score = EMBEDDING_UNKNOWN_LABEL, -1.0
    for name, ref_embeddings in database.items():
        for ref in ref_embeddings:
            score = cosine_sim(embedding, ref)
            if score > best_score:
                best_name, best_score = name, score
    return best_name, best_score


def run(source, db_path: str, weights: str, show: bool, conf: float):
    with open(db_path, "rb") as f:
        database = pickle.load(f)
    print(f"Loaded {len(database)} known identities from {db_path}")

    detector = YOLO(weights)                 # e.g. "yolo26n.pt" or "yolo26m.pt"
    face_app = FaceAnalysis(name="buffalo_l")
    face_app.prepare(ctx_id=0, det_size=(320, 320))  # smaller det_size = faster on crops

    track_states: dict[int, TrackState] = {}

    # model.track() runs YOLO26 detection + ByteTrack tracking together and
    # yields results with a persistent .id per box across the stream.
    results_stream = detector.track(
        source=source,
        classes=[COCO_PERSON_CLASS_ID],
        tracker="bytetrack.yaml",
        conf=conf,
        persist=True,
        stream=True,
        verbose=False,
    )

    for frame_result in results_stream:
        frame = frame_result.orig_img
        boxes = frame_result.boxes

        if boxes is None or boxes.id is None:
            if show:
                cv2.imshow("tracking", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            continue

        ids = boxes.id.int().cpu().tolist()
        xyxy = boxes.xyxy.cpu().numpy()

        for track_id, (x1, y1, x2, y2) in zip(ids, xyxy):
            x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
            x1, y1 = max(0, x1), max(0, y1)
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            state = track_states.setdefault(track_id, TrackState())

            # Only run recognition periodically per track, and stop once confidently matched.
            should_check = (
                state.label is None
                or state.label == EMBEDDING_UNKNOWN_LABEL
                or state.frames_since_check >= RECOGNITION_INTERVAL
            )

            if should_check:
                state.frames_since_check = 0
                faces = face_app.get(crop)
                if faces:
                    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                    name, score = match_face(face.normed_embedding, database)
                    if score >= MATCH_THRESHOLD and score > state.best_score:
                        state.label = name
                        state.best_score = score
                    elif state.label is None:
                        state.label = EMBEDDING_UNKNOWN_LABEL
            else:
                state.frames_since_check += 1

            label = state.label or EMBEDDING_UNKNOWN_LABEL
            display = f"ID {track_id}: {label}"
            if state.best_score > 0:
                display += f" ({state.best_score:.2f})"

            color = (0, 200, 0) if label != EMBEDDING_UNKNOWN_LABEL else (0, 165, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, display, (x1, max(0, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        if show:
            cv2.imshow("tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    if show:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, required=True, help="RTSP URL, video file, or webcam index")
    parser.add_argument("--db", type=str, default="face_db.pkl", help="Path to enrolled face database")
    parser.add_argument("--weights", type=str, default="yolo26n.pt", help="YOLO26 weights (n/s/m/l/x)")
    parser.add_argument("--conf", type=float, default=0.4, help="Detection confidence threshold")
    parser.add_argument("--show", action="store_true", help="Display annotated video window")
    args = parser.parse_args()

    run(args.source, args.db, args.weights, args.show, args.conf)
