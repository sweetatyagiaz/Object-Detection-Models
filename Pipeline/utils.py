"""
Reusable utilities for SCRFD face detection + RF-DETR car detection.

Keep model initialization, inference, annotation, and per-image processing here.
Dataset traversal and batch orchestration live in create_dataset.py.
"""

import json
import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from insightface.model_zoo import get_model
from rfdetr import RFDETRSmall


# ---------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------

DEFAULT_SCRFD_MODEL = Path("/home/rakesh/AI_Models/scrfd_34g.onnx")
DEFAULT_FACE_THRESHOLD = 0.40
DEFAULT_CAR_THRESHOLD = 0.45
DEFAULT_FACE_INPUT_SIZE = (640, 640)
DEFAULT_SCRFD_DEVICE_ID = -1  # -1 = CPU; 0 = first CUDA device


def configure_logging(level=logging.INFO):
    """Configure a consistent logger for scripts using these utilities."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    return logging.getLogger("face-car-detection")


def load_face_detector(
    model_path=DEFAULT_SCRFD_MODEL,
    device_id=DEFAULT_SCRFD_DEVICE_ID,
    input_size=DEFAULT_FACE_INPUT_SIZE,
):
    """Load an InsightFace-compatible SCRFD ONNX detector."""
    model_path = Path(model_path)

    if not model_path.is_file():
        raise FileNotFoundError(
            f"SCRFD ONNX model not found: {model_path}. "
            "Check that this is the converted SCRFD_34G ONNX model."
        )

    logger = logging.getLogger("face-car-detection")
    logger.info("Loading SCRFD face detector from %s", model_path)

    detector = get_model(str(model_path))
    if detector is None:
        raise RuntimeError(f"Could not load SCRFD model: {model_path}")

    detector.prepare(ctx_id=device_id, input_size=input_size)
    logger.info("SCRFD face detector loaded.")
    return detector


def load_car_detector():
    """Load the RF-DETR Small COCO-pretrained detector."""
    logger = logging.getLogger("face-car-detection")
    logger.info("Loading RF-DETR Small car detector...")
    detector = RFDETRSmall()
    logger.info("RF-DETR loaded.")
    return detector


def detect_faces(
    image,
    face_detector,
    confidence_threshold=DEFAULT_FACE_THRESHOLD,
    max_num=0,
):
    """
    Detect faces in an OpenCV BGR image.

    InsightFace SCRFD's API takes the confidence threshold as a positional
    argument: detect(image, threshold, max_num=...).
    """
    faces, _ = face_detector.detect(
        image,
        confidence_threshold,
        max_num=max_num,
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
                round(float(y2), 2),
            ],
        })

    return results


def get_class_name(class_names, class_id):
    """Resolve an RF-DETR class ID to its class label."""
    if isinstance(class_names, dict):
        return str(class_names.get(class_id, class_names.get(str(class_id), "")))

    if isinstance(class_names, (list, tuple)):
        if 0 <= class_id < len(class_names):
            return str(class_names[class_id])

    return ""


def detect_cars(
    image,
    car_detector,
    confidence_threshold=DEFAULT_CAR_THRESHOLD,
):
    """Detect cars in an OpenCV BGR image using RF-DETR."""
    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    detections = car_detector.predict(
        pil_image,
        threshold=confidence_threshold,
    )

    results = []
    class_names = getattr(car_detector, "class_names", None)

    boxes = detections.xyxy
    confidences = detections.confidence
    class_ids = detections.class_id

    if boxes is None:
        return results

    for box, confidence, class_id in zip(boxes, confidences, class_ids):
        class_id = int(class_id)
        label = get_class_name(class_names, class_id).strip().lower()

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
                round(y2, 2),
            ],
        })

    return results


def annotate_image(image, detections, box_thickness=2):
    """Draw face and car bounding boxes on an OpenCV BGR image."""
    output = image.copy()

    for detection in detections:
        x1, y1, x2, y2 = map(int, detection["bbox"])
        label = detection["class"]
        confidence = detection["confidence"]

        color = (0, 255, 0) if label == "face" else (255, 100, 0)

        cv2.rectangle(
            output,
            (x1, y1),
            (x2, y2),
            color,
            box_thickness,
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
            cv2.LINE_AA,
        )

    return output


def process_image(
    image_path,
    input_dir,
    output_dir,
    face_detector,
    car_detector,
    face_threshold=DEFAULT_FACE_THRESHOLD,
    car_threshold=DEFAULT_CAR_THRESHOLD,
    save_json=True,
    save_annotated_image=True,
):
    """
    Process one image and preserve its relative directory structure.

    Returns a result dictionary, or None when OpenCV cannot read the image.
    """
    image_path = Path(image_path)
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    relative_path = image_path.relative_to(input_dir)
    output_image_path = output_dir / relative_path
    output_json_path = output_image_path.with_suffix(".json")

    output_image_path.parent.mkdir(parents=True, exist_ok=True)

    image = cv2.imread(str(image_path))
    if image is None:
        logging.getLogger("face-car-detection").warning(
            "Unable to read image: %s", image_path
        )
        return None

    height, width = image.shape[:2]

    face_results = detect_faces(
        image,
        face_detector,
        confidence_threshold=face_threshold,
    )
    car_results = detect_cars(
        image,
        car_detector,
        confidence_threshold=car_threshold,
    )
    all_detections = face_results + car_results

    if save_annotated_image:
        annotated = annotate_image(image, all_detections)
        if not cv2.imwrite(str(output_image_path), annotated):
            raise RuntimeError(f"Failed to save image: {output_image_path}")

    json_data = {
        "image": str(relative_path),
        "image_width": width,
        "image_height": height,
        "summary": {
            "faces": len(face_results),
            "cars": len(car_results),
            "total_objects": len(all_detections),
        },
        "detections": all_detections,
    }

    if save_json:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        with output_json_path.open("w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=4)

    logging.getLogger("face-car-detection").info(
        "Processed: %s | Faces: %d | Cars: %d",
        relative_path,
        len(face_results),
        len(car_results),
    )

    return json_data
