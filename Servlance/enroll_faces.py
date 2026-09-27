"""
enroll_faces.py

Builds a local face-embedding database from a folder of reference photos.

Expected folder layout:

    database/
        alice/
            alice_1.jpg
            alice_2.jpg
        bob/
            bob_1.jpg
        ...

One or more photos per person improves matching accuracy (different angles/lighting).
Each subfolder name becomes the identity label.

Usage:
    python enroll_faces.py --input database --output face_db.pkl
    python enroll_faces.py --input ../database --output ../database/face_db.pk
"""

import argparse
import pickle
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis


def build_database(input_dir: Path, output_path: Path, det_size=(640, 640)):
    # buffalo_l bundles a face detector (SCRFD) + ArcFace recognition model.
    # ctx_id=0 uses GPU 0 if available; falls back to CPU automatically if not.
    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=0, det_size=det_size)

    database = {}  # name -> list of embeddings (np.ndarray, 512-d)

    for person_dir in sorted(input_dir.iterdir()):
        if not person_dir.is_dir():
            continue
        name = person_dir.name
        embeddings = []

        for img_path in sorted(person_dir.glob("*")):
            if img_path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"  [skip] could not read {img_path}")
                continue

            faces = app.get(img)
            if not faces:
                print(f"  [skip] no face found in {img_path}")
                continue
            if len(faces) > 1:
                print(f"  [warn] multiple faces in {img_path}, using the largest")

            # Pick the largest detected face (by box area) as the reference face.
            face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            embeddings.append(face.normed_embedding)  # already L2-normalized, 512-d

        if embeddings:
            database[name] = embeddings
            print(f"[ok] enrolled '{name}' with {len(embeddings)} reference image(s)")
        else:
            print(f"[warn] no usable faces found for '{name}', skipped")

    with open(output_path, "wb") as f:
        pickle.dump(database, f)
    print(f"\nSaved database with {len(database)} identities -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="known_faces", help="Folder of per-person subfolders")
    parser.add_argument("--output", type=str, default="face_db.pkl", help="Output pickle path")
    args = parser.parse_args()

    build_database(Path(args.input), Path(args.output))
