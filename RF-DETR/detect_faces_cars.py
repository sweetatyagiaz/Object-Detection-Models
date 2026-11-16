
import cv2
import json
import logging
import numpy as np

from pathlib import Path
from PIL import Image
from insightface.model_zoo import get_model
from rfdetr import RFDETRSmall


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path("/home/rakesh/datasets/raw_data")
OUTPUT_DIR = Path("/home/rakesh/datasets/dataset_rf_detr")

SCRFD_MODEL = Path(
    "/home/rakesh/AI_Models/scrfd_34g.onnx"
)

FACE_THRESHOLD = 0.40
CAR_THRESHOLD = 0.45

FACE_INPUT_SIZE = (640, 640)

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp",
    ".tif", ".tiff", ".webp"
}

# Set to -1 for CPU.
# Use 0 for GPU when the required CUDA providers are installed.
SCRFD_DEVICE_ID = -1

# RF-DETR model choice
RFDETR_DEVICE = "cpu"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("face-car-detection")


# ============================================================
# MODEL INITIALIZATION
# ============================================================

def load_face_detector():

    if not SCRFD_MODEL.exists():
        raise FileNotFoundError(
            f"SCRFD_34G ONNX model not found: {SCRFD_MODEL}\n"
            "Convert the original SCRFD_34G checkpoint to ONNX first."
        )

    logger.info("Loading SCRFD_34G face detector...")

    detector = get_model(str(SCRFD_MODEL))

    if detector is None:
        raise RuntimeError("Could not load SCRFD ONNX model.")

    detector.prepare(
        ctx_id=SCRFD_DEVICE_ID,
        input_size=FACE_INPUT_SIZE
    )

    logger.info("SCRFD_34G loaded successfully.")

    return detector


def load_car_detector():

    logger.info("Loading RF-DETR car detector...")

    model = RFDETRSmall()

    logger.info("RF-DETR loaded successfully.")

    return model


# ============================================================
# FACE DETECTION
# ============================================================


def detect_faces(image, face_detector):

    # SCRFD API:
    # detect(img, threshold, max_num=0, metric="default")
    faces, _ = face_detector.detect(
        image,
        FACE_THRESHOLD,
        max_num=0
    )

    results = []

    if faces is None:
        return results

    for face in faces:

        x1, y1, x2, y2 = face[:4]
        confidence = float(face[4])

        results.append({
            "class": "face",
            "confidence": confidence,
            "bbox": [
                round(float(x1), 2),
                round(float(y1), 2),
                round(float(x2), 2),
                round(float(y2), 2)
            ]
        })

    return results


# ============================================================
# CAR DETECTION
# ============================================================

def get_class_name(class_names, class_id):

    if isinstance(class_names, dict):
        return str(class_names.get(class_id, ""))

    if isinstance(class_names, (list, tuple)):
        if 0 <= class_id < len(class_names):
            return str(class_names[class_id])

    return ""


def detect_cars(image, car_detector):

    # RF-DETR expects a PIL image.
    pil_image = Image.fromarray(
        cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    )

    detections = car_detector.predict(
        pil_image,
        threshold=CAR_THRESHOLD
    )

    results = []

    class_names = getattr(
        car_detector,
        "class_names",
        None
    )

    boxes = detections.xyxy
    confidences = detections.confidence
    class_ids = detections.class_id

    if boxes is None:
        return results

    for box, confidence, class_id in zip(
        boxes,
        confidences,
        class_ids
    ):

        class_id = int(class_id)

        label = get_class_name(
            class_names,
            class_id
        ).lower()

        # RF-DETR COCO pretrained model:
        # retain only detections identified as car.
        if label != "car":
            continue

        x1, y1, x2, y2 = map(float, box)

        results.append({
            "class": "car",
            "confidence": float(confidence),
            "bbox": [
                round(x1, 2),
                round(y1, 2),
                round(x2, 2),
                round(y2, 2)
            ]
        })

    return results


# ============================================================
# IMAGE ANNOTATION
# ============================================================

def annotate_image(image, detections):

    output = image.copy()

    for detection in detections:

        x1, y1, x2, y2 = map(
            int,
            detection["bbox"]
        )

        label = detection["class"]
        confidence = detection["confidence"]

        if label == "face":
            color = (0, 255, 0)
        else:
            color = (255, 100, 0)

        cv2.rectangle(
            output,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        text = f"{label}: {confidence:.2f}"

        cv2.putText(
            output,
            text,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA
        )

    return output


# ============================================================
# PROCESS ONE IMAGE
# ============================================================

def process_image(
    image_path,
    face_detector,
    car_detector
):

    relative_path = image_path.relative_to(INPUT_DIR)

    output_image_path = OUTPUT_DIR / relative_path

    output_json_path = output_image_path.with_suffix(".json")

    output_image_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    image = cv2.imread(str(image_path))

    if image is None:
        logger.warning("Unable to read: %s", image_path)
        return

    height, width = image.shape[:2]

    # Face detection
    face_results = detect_faces(
        image,
        face_detector
    )

    # Car detection
    car_results = detect_cars(
        image,
        car_detector
    )

    all_detections = face_results + car_results

    # Annotated image
    annotated = annotate_image(
        image,
        all_detections
    )

    if not cv2.imwrite(
        str(output_image_path),
        annotated
    ):
        raise RuntimeError(
            f"Failed to save image: {output_image_path}"
        )

    # JSON output
    json_data = {
        "image": str(relative_path),
        "image_width": width,
        "image_height": height,
        "summary": {
            "faces": len(face_results),
            "cars": len(car_results),
            "total_objects": len(all_detections)
        },
        "detections": all_detections
    }

    with open(
        output_json_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            json_data,
            file,
            indent=4
        )

    logger.info(
        "Processed: %s | Faces: %d | Cars: %d",
        relative_path,
        len(face_results),
        len(car_results)
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    if not INPUT_DIR.exists():
        raise FileNotFoundError(
            f"Input directory does not exist: {INPUT_DIR}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Initialize models only once.
    face_detector = load_face_detector()
    car_detector = load_car_detector()

    image_files = [
        path
        for path in INPUT_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ]

    logger.info(
        "Total images found: %d",
        len(image_files)
    )

    processed = 0
    failed = 0

    for image_path in image_files:

        try:

            process_image(
                image_path,
                face_detector,
                car_detector
            )

            processed += 1

        except Exception:

            failed += 1

            logger.exception(
                "Failed processing: %s",
                image_path
            )

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETED")
    logger.info("Total images: %d", len(image_files))
    logger.info("Processed: %d", processed)
    logger.info("Failed: %d", failed)
    logger.info("Output: %s", OUTPUT_DIR)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
