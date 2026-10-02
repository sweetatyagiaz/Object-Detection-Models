
from pathlib import Path

import cv2
import pandas as pd
from tqdm import tqdm

from insightface.app import FaceAnalysis


# =============================================================================
# CONFIGURATION
# =============================================================================

RAW_DATA_PATH = "../datasets/raw_data"

REPORTS_DIR = "../datasets/results/SCRFD/reports"
PREVIEW_DIR = "../datasets/results/SCRFD/previews"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

# Quality thresholds

MIN_CONFIDENCE = 0.70
MIN_FACE_WIDTH = 80
MIN_FACE_HEIGHT = 80
MIN_BLUR_SCORE = 100


# =============================================================================
# HELPERS
# =============================================================================

def blur_score(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def brightness_score(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray.mean()


def largest_face(faces):
    return max(
        faces,
        key=lambda face:
        (face.bbox[2] - face.bbox[0]) *
        (face.bbox[3] - face.bbox[1])
    )


def classify(
    face_count,
    confidence,
    face_width,
    face_height,
    blur,
    brightness
):
    reasons = []

    if face_count == 0:
        return "REMOVE", "NO_FACE"

    if face_count > 1:
        reasons.append("MULTIPLE_FACES")

    if confidence < MIN_CONFIDENCE:
        reasons.append("LOW_CONFIDENCE")

    if face_width < MIN_FACE_WIDTH:
        reasons.append("FACE_TOO_SMALL")

    if face_height < MIN_FACE_HEIGHT:
        reasons.append("FACE_TOO_SMALL")

    if blur < MIN_BLUR_SCORE:
        reasons.append("BLURRY")

    if brightness < 40:
        reasons.append("TOO_DARK")

    if brightness > 220:
        reasons.append("OVER_EXPOSED")

    if not reasons:
        return "KEEP", "GOOD_QUALITY"

    critical = {
        "LOW_CONFIDENCE",
        "FACE_TOO_SMALL"
    }

    if any(reason in critical for reason in reasons):
        return "REMOVE", ",".join(reasons)

    return "REVIEW", ",".join(reasons)


def create_preview(
    image,
    action,
    confidence,
    blur,
    brightness,
    face_width,
    face_height,
    output_path,
    bbox=None
):
    preview = image.copy()

    if bbox is not None:
        x1, y1, x2, y2 = bbox
        cv2.rectangle(
            preview,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

    lines = [
        f"Action: {action}",
        f"Conf: {confidence:.3f}",
        f"Blur: {blur:.1f}",
        f"Bright: {brightness:.1f}",
        f"Face: {face_width}x{face_height}"
    ]

    y = 30

    for line in lines:
        cv2.putText(
            preview,
            line,
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        y += 30

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cv2.imwrite(
        str(output_path),
        preview
    )


# =============================================================================
# MAIN
# =============================================================================

def main():

    raw_data = Path(RAW_DATA_PATH)

    reports_dir = Path(REPORTS_DIR)
    reports_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    preview_dir = Path(PREVIEW_DIR)

    detector = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )

    detector.prepare(
        ctx_id=0,
        det_size=(640, 640)
    )

    image_files = []

    for ext in SUPPORTED_EXTENSIONS:
        image_files.extend(
            raw_data.rglob(f"*{ext}")
        )
        image_files.extend(
            raw_data.rglob(f"*{ext.upper()}")
        )

    rows = []

    for image_path in tqdm(
        sorted(image_files),
        desc="Auditing Dataset"
    ):

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            continue

        image_height, image_width = image.shape[:2]

        blur = blur_score(image)
        brightness = brightness_score(image)

        relative_path = image_path.relative_to(raw_data)

        person_name = (
            relative_path.parts[0]
            if len(relative_path.parts) > 1
            else "unknown"
        )

        faces = detector.get(image)

        if len(faces) == 0:

            action, reason = classify(
                0, 0, 0, 0,
                blur,
                brightness
            )

            preview_file = (
                preview_dir /
                action.lower() /
                relative_path
            )

            create_preview(
                image=image,
                action=action,
                confidence=0,
                blur=blur,
                brightness=brightness,
                face_width=0,
                face_height=0,
                output_path=preview_file
            )

            rows.append({
                "person": person_name,
                "file": str(relative_path),
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

        face = largest_face(faces)

        x1, y1, x2, y2 = (
            face.bbox.astype(int)
        )

        face_width = x2 - x1
        face_height = y2 - y1

        confidence = float(face.det_score)

        action, reason = classify(
            len(faces),
            confidence,
            face_width,
            face_height,
            blur,
            brightness
        )

        preview_file = (
            preview_dir /
            action.lower() /
            relative_path
        )

        create_preview(
            image=image,
            action=action,
            confidence=confidence,
            blur=blur,
            brightness=brightness,
            face_width=face_width,
            face_height=face_height,
            output_path=preview_file,
            bbox=(x1, y1, x2, y2)
        )

        rows.append({
            "person": person_name,
            "file": str(relative_path),
            "faces": len(faces),
            "confidence": round(confidence, 4),
            "face_width": face_width,
            "face_height": face_height,
            "blur_score": round(blur, 2),
            "brightness": round(brightness, 2),
            "action": action,
            "reason": reason
        })

    df = pd.DataFrame(rows)

    csv_file = reports_dir / "dataset_quality.csv"
    html_file = reports_dir / "dataset_quality.html"

    df.to_csv(
        csv_file,
        index=False
    )

    html = f"""
    <html>
    <head>
        <title>Dataset Quality Report</title>
        <style>
            body {{
                font-family: Arial;
                margin: 20px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
            }}
            th {{
                background: #f0f0f0;
            }}
        </style>
    </head>
    <body>
        <h1>Dataset Quality Report</h1>
        <h3>Total Images: {len(df)}</h3>
        {df.to_html(index=False)}
    </body>
    </html>
    """

    with open(
        html_file,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(html)

    print("\n" + "=" * 80)
    print("AUDIT COMPLETED")
    print("=" * 80)
    print(f"Images Analysed : {len(df)}")
    print(f"CSV Report      : {csv_file}")
    print(f"HTML Report     : {html_file}")
    print(f"Preview Folder  : {preview_dir}")
    print("\nAction Summary")
    print(df["action"].value_counts())
    print("=" * 80)


if __name__ == "__main__":
    main()
