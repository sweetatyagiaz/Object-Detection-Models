
import cv2
import faiss
import numpy as np
from collections import defaultdict


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