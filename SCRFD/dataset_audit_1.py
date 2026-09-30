from pathlib import Path
import cv2
import pandas as pd
from tqdm import tqdm
from insightface.app import FaceAnalysis

DATASET_PATH = "../datasets/raw_data"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


def blur_score(image):
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    return cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()


def brightness_score(image):
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    return gray.mean()


def recommendation(
    face_count,
    confidence,
    face_width,
    blur,
    brightness,
):
    reasons = []

    if face_count == 0:
        return "REMOVE", "NO_FACE"

    if face_count > 1:
        reasons.append("MULTIPLE_FACES")

    if confidence < 0.70:
        reasons.append("LOW_CONFIDENCE")

    if face_width < 80:
        reasons.append("FACE_TOO_SMALL")

    if blur < 100:
        reasons.append("BLURRY")

    if brightness < 40:
        reasons.append("TOO_DARK")

    if brightness > 220:
        reasons.append("OVER_EXPOSED")

    if len(reasons) == 0:
        return "KEEP", "GOOD_QUALITY"

    if (
        "LOW_CONFIDENCE" in reasons
        or "FACE_TOO_SMALL" in reasons
    ):
        return "REMOVE", ",".join(reasons)

    return "REVIEW", ",".join(reasons)


def main():

    detector = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )

    detector.prepare(
        ctx_id=0,
        det_size=(640, 640)
    )

    rows = []

    dataset_path = Path(DATASET_PATH)

    image_files = []

    for ext in SUPPORTED_EXTENSIONS:
        image_files.extend(
            dataset_path.rglob(f"*{ext}")
        )

    for image_path in tqdm(image_files):

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            continue

        height, width = image.shape[:2]

        blur = blur_score(image)
        brightness = brightness_score(image)

        faces = detector.get(image)

        if len(faces) == 0:

            action, reason = recommendation(
                0,
                0,
                0,
                blur,
                brightness
            )

            rows.append({
                "file": str(image_path),
                "image_width": width,
                "image_height": height,
                "faces": 0,
                "confidence": 0,
                "face_width": 0,
                "face_height": 0,
                "blur_score": round(blur, 2),
                "brightness": round(brightness, 2),
                "action": action,
                "reason": reason
            })

            continue

        largest_face = max(
            faces,
            key=lambda face:
            (face.bbox[2]-face.bbox[0])
            *
            (face.bbox[3]-face.bbox[1])
        )

        x1, y1, x2, y2 = (
            largest_face.bbox.astype(int)
        )

        face_width = x2 - x1
        face_height = y2 - y1

        action, reason = recommendation(
            len(faces),
            float(largest_face.det_score),
            face_width,
            blur,
            brightness
        )

        rows.append({
            "file": str(image_path),
            "image_width": width,
            "image_height": height,
            "faces": len(faces),
            "confidence": round(
                float(largest_face.det_score),
                4
            ),
            "face_width": face_width,
            "face_height": face_height,
            "blur_score": round(blur, 2),
            "brightness": round(brightness, 2),
            "action": action,
            "reason": reason
        })

    df = pd.DataFrame(rows)

    report_file = "../datasets/dataset_quality_report.csv"

    df.to_csv(
        report_file,
        index=False
    )

    print()
    print("=" * 80)
    print("DATASET AUDIT COMPLETED")
    print("=" * 80)
    print(f"Images Analysed : {len(df)}")
    print()
    print(df["action"].value_counts())
    print()
    print(f"Report Saved : {report_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()