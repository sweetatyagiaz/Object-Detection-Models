import cv2
import faiss
import numpy as np
from collections import defaultdict

from adaface import AdaFace


MODEL_PATH = "../models/adaface_ir50.onnx"
DATABASE_DIR = "../datasets/dataset_deepface"

INDEX_PATH = "../datasets/faiss_indexes/face_index_adaface.bin"
MAPPING_PATH = "../datasets/faiss_indexes/mapping_adaface.json"


THRESHOLD = 0.40
TOP_K = 1


adaface = AdaFace(
    model_path=MODEL_PATH,
    database_dir=DATABASE_DIR,
    index_path=INDEX_PATH,
    mapping_path=MAPPING_PATH,
)

adaface.load_index()


def recognize_face(face_image):

    result = adaface.get_embedding(face_image)

    if result is None:
        return None

    embedding, quality = result

    embedding = embedding.reshape(1, -1).astype(np.float32)

    scores, indices = adaface.index.search(
        embedding,
        20
    )

    persons = defaultdict(list)

    for score, idx in zip(scores[0], indices[0]):

        if idx < 0:
            continue

        meta = adaface.mapping[idx]

        persons[meta["person_id"]].append(
            {
                "score": float(score),
                "name": meta["name"]
            }
        )

    if not persons:
        return None

    results = []

    for pid, matches in persons.items():

        matches.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        best = matches[0]

        results.append(
            {
                "person_id": pid,
                "name": best["name"],
                "score": best["score"]
            }
        )

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    best_match = results[0]

    if best_match["score"] < THRESHOLD:
        return None

    return best_match













cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Cannot open webcam")


while True:

    ret, frame = cap.read()

    if not ret:
        break

    faces = adaface.detector.get(frame)

    for face in faces:

        x1, y1, x2, y2 = map(
            int,
            face.bbox
        )

        crop = frame[
            max(0, y1):max(0, y2),
            max(0, x1):max(0, x2)
        ]

        if crop.size == 0:
            continue

        result = recognize_face(crop)

        if result:

            label = (
                f"{result['name']} "
                f"{result['score']:.2f}"
            )

            color = (0, 255, 0)

        else:

            label = "Unknown"
            color = (0, 0, 255)

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )

    cv2.imshow(
        "AdaFace Recognition",
        frame
    )

    key = cv2.waitKey(1)

    if key == 27:
        break


cap.release()
cv2.destroyAllWindows()