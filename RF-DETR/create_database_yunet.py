
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from insightface.model_zoo import get_model
from rfdetr import RFDETRSmall

# RF-DETR class list import compatibility
try:
    from rfdetr.assets.coco_classes import COCO_CLASSES
except ImportError:
    from rfdetr.util.coco_classes import COCO_CLASSES


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("RF-DETR")


# =========================================================
# CONFIGURATION
# =========================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff",
}


# =========================================================
# SCRFD FACE DETECTOR
# =========================================================

def load_face_detector(
    model_path,
    detection_size=640,
    confidence_threshold=0.50,
    nms_threshold=0.40,
):
    """
    Load a SCRFD ONNX face detector.

    Args:
        model_path: SCRFD ONNX model path.
        detection_size: Detector input width and height.
        confidence_threshold: Minimum face confidence.
        nms_threshold: SCRFD NMS threshold.

    Returns:
        Initialized SCRFD detector.
    """

    model_path = Path(model_path).expanduser()

    if not model_path.is_file():
        raise FileNotFoundError(
            f"SCRFD model not found: {model_path}"
        )

    logger.info("Loading SCRFD model: %s", model_path)

    detector = get_model(str(model_path))

    if detector is None:
        raise RuntimeError(
            "Could not initialize SCRFD model. "
            "Check that the ONNX file is a compatible SCRFD detector."
        )

    detector.prepare(
        ctx_id=-1,
        input_size=(detection_size, detection_size),
        det_thresh=confidence_threshold,
        nms_thresh=nms_threshold,
    )

    logger.info(
        "SCRFD loaded | Input: %dx%d | Confidence: %.2f | NMS: %.2f",
        detection_size,
        detection_size,
        confidence_threshold,
        nms_threshold,
    )

    return detector


# =========================================================
# SCRFD FACE DETECTION
# =========================================================

def detect_faces(
    image,
    face_detector,
    detection_size=640,
    confidence_threshold=0.50,
):
    """
    Detect faces using SCRFD.

    Returns bounding boxes and five facial landmarks.
    Coordinates are relative to the original image.
    """

    if image is None:
        return []

    # Use the model's native detection pipeline.
    # SCRFD performs its own NMS internally.
    boxes, landmarks = face_detector.detect(
        image,
        input_size=(detection_size, detection_size),
        max_num=0,
        metric="default",
    )

    results = []

    if boxes is None or len(boxes) == 0:
        return results

    image_height, image_width = image.shape[:2]

    for index, box in enumerate(boxes):

        x1, y1, x2, y2, confidence = box[:5]

        confidence = float(confidence)

        if confidence < confidence_threshold:
            continue

        x1 = max(0, min(int(round(x1)), image_width - 1))
        y1 = max(0, min(int(round(y1)), image_height - 1))
        x2 = max(0, min(int(round(x2)), image_width))
        y2 = max(0, min(int(round(y2)), image_height))

        if x2 <= x1 or y2 <= y1:
            continue

        face_landmarks = []

        if landmarks is not None and len(landmarks) > index:

            for point in landmarks[index]:
                px, py = point

                face_landmarks.append([
                    float(px),
                    float(py),
                ])

        results.append({
            "class": "face",
            "confidence": confidence,
            "bbox": [x1, y1, x2, y2],
            "landmarks": face_landmarks,
        })

    return results


# =========================================================
# RF-DETR CAR DETECTOR
# =========================================================

def load_car_detector(weights_path=None):

    logger.info("Loading RF-DETR Small...")

    if weights_path:

        weights_path = Path(weights_path).expanduser()

        if not weights_path.is_file():
            raise FileNotFoundError(
                f"RF-DETR weights not found: {weights_path}"
            )

        detector = RFDETRSmall(
            pretrain_weights=str(weights_path)
        )

    else:
        detector = RFDETRSmall()

    logger.info("RF-DETR loaded.")

    return detector


# =========================================================
# RF-DETR CLASS NAME RESOLUTION
# =========================================================

def get_class_name(detections, index, class_id):
    """
    Resolve class name from detection metadata.

    Fine-tuned models should use data['class_name'].
    COCO-pretrained models use COCO_CLASSES.
    """

    data = getattr(detections, "data", {}) or {}

    if "class_name" in data:

        name = data["class_name"][index]

        if isinstance(name, bytes):
            name = name.decode("utf-8")

        return str(name).strip().lower()

    class_id = int(class_id)

    if isinstance(COCO_CLASSES, dict):
        return str(
            COCO_CLASSES.get(class_id, class_id)
        ).lower()

    try:
        return str(COCO_CLASSES[class_id]).lower()

    except (IndexError, KeyError, TypeError):
        return str(class_id).lower()


# =========================================================
# CAR DETECTION
# =========================================================

def detect_cars(
    image,
    car_detector,
    confidence_threshold=0.50,
):
    """
    Detect cars using RF-DETR.
    """

    rgb_image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB,
    )

    detections = car_detector.predict(
        rgb_image,
        threshold=confidence_threshold,
    )

    results = []

    boxes = detections.xyxy
    scores = detections.confidence
    class_ids = detections.class_id

    if boxes is None or len(boxes) == 0:
        return results

    if scores is None or class_ids is None:
        return results

    image_height, image_width = image.shape[:2]

    for index, (box, score, class_id) in enumerate(
        zip(boxes, scores, class_ids)
    ):

        class_name = get_class_name(
            detections,
            index,
            class_id,
        )

        if class_name != "car":
            continue

        x1, y1, x2, y2 = [
            int(round(float(value)))
            for value in box
        ]

        x1 = max(0, min(x1, image_width - 1))
        y1 = max(0, min(y1, image_height - 1))
        x2 = max(0, min(x2, image_width))
        y2 = max(0, min(y2, image_height))

        if x2 <= x1 or y2 <= y1:
            continue

        results.append({
            "class": "car",
            "confidence": float(score),
            "bbox": [x1, y1, x2, y2],
        })

    return results


# =========================================================
# DRAW DETECTIONS
# =========================================================

def annotate_image(
    image,
    detections,
    draw_landmarks=True,
):
    """
    Draw face and car bounding boxes.
    """

    annotated = image.copy()

    for detection in detections:

        x1, y1, x2, y2 = detection["bbox"]

        class_name = detection["class"]
        confidence = detection["confidence"]

        if class_name == "face":
            color = (0, 255, 0)
        else:
            color = (255, 165, 0)

        cv2.rectangle(
            annotated,
            (x1, y1),
            (x2, y2),
            color,
            2,
        )

        label = f"{class_name}: {confidence:.2f}"

        label_y = max(20, y1 - 8)

        cv2.putText(
            annotated,
            label,
            (x1, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )

        # Draw SCRFD facial landmarks.
        if (
            class_name == "face"
            and draw_landmarks
        ):
            for point in detection.get("landmarks", []):

                px, py = point

                cv2.circle(
                    annotated,
                    (int(round(px)), int(round(py))),
                    3,
                    (0, 0, 255),
                    -1,
                )

    return annotated


# =========================================================
# PROCESS SINGLE IMAGE
# =========================================================

def process_image(
    image_path,
    output_path,
    face_detector,
    car_detector,
    face_detection_size,
    face_threshold,
    car_threshold,
):
    """
    Process one image:
      1. Load image
      2. Detect faces
      3. Detect cars
      4. Annotate image
      5. Save image
      6. Save JSON
    """

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(
            f"Unable to read image: {image_path}"
        )

    # Face detection using SCRFD.
    face_detections = detect_faces(
        image,
        face_detector,
        detection_size=face_detection_size,
        confidence_threshold=face_threshold,
    )

    # Car detection using RF-DETR.
    car_detections = detect_cars(
        image,
        car_detector,
        confidence_threshold=car_threshold,
    )

    all_detections = (
        face_detections + car_detections
    )

    # Annotate.
    annotated_image = annotate_image(
        image,
        all_detections,
        draw_landmarks=True,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save annotated image.
    success = cv2.imwrite(
        str(output_path),
        annotated_image,
    )

    if not success:
        raise IOError(
            f"Unable to save image: {output_path}"
        )

    # Save JSON alongside the annotated image.
    json_path = output_path.with_name(
        output_path.name + ".detections.json"
    )

    image_height, image_width = image.shape[:2]

    json_data = {
        "input_image": str(image_path),
        "output_image": str(output_path),
        "image_width": image_width,
        "image_height": image_height,
        "processed_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "face_detector": "SCRFD",
        "car_detector": "RF-DETR",
        "total_faces": len(face_detections),
        "total_cars": len(car_detections),
        "total_detections": len(all_detections),
        "detections": all_detections,
    }

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            json_data,
            file,
            indent=4,
        )

    return {
        "input": str(image_path),
        "output": str(output_path),
        "json": str(json_path),
        "faces": len(face_detections),
        "cars": len(car_detections),
        "total": len(all_detections),
        "status": "success",
    }


# =========================================================
# FIND IMAGES RECURSIVELY
# =========================================================

def find_images(input_dir):

    return sorted(
        path
        for path in input_dir.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
        )
    )


# =========================================================
# MAIN
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Face detection with SCRFD and car detection "
            "with RF-DETR. Recursively processes directories."
        )
    )

    parser.add_argument(
        "--input-dir",
        required=True,
        help="Input directory containing images.",
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for annotated images and JSON.",
    )

    parser.add_argument(
        "--face-model",
        required=True,
        help="Path to SCRFD ONNX model.",
    )

    parser.add_argument(
        "--rfdetr-weights",
        default=None,
        help="Optional RF-DETR weights path.",
    )

    parser.add_argument(
        "--face-threshold",
        type=float,
        default=0.50,
        help="SCRFD confidence threshold.",
    )

    parser.add_argument(
        "--car-threshold",
        type=float,
        default=0.50,
        help="RF-DETR confidence threshold.",
    )

    parser.add_argument(
        "--face-input-size",
        type=int,
        default=640,
        help="SCRFD square input size. Default: 640.",
    )

    args = parser.parse_args()

    # Validate thresholds and dimensions.
    if not 0.0 <= args.face_threshold <= 1.0:
        parser.error("--face-threshold must be between 0 and 1.")

    if not 0.0 <= args.car_threshold <= 1.0:
        parser.error("--car-threshold must be between 0 and 1.")

    if args.face_input_size <= 0:
        parser.error("--face-input-size must be positive.")

    input_dir = Path(
        args.input_dir
    ).expanduser().resolve()

    output_dir = Path(
        args.output_dir
    ).expanduser().resolve()

    if not input_dir.is_dir():
        parser.error(
            f"Input directory does not exist: {input_dir}"
        )

    if input_dir == output_dir:
        parser.error(
            "Input and output directories must be different."
        )

    # Prevent recursive processing of output images.
    try:
        output_dir.relative_to(input_dir)

        parser.error(
            "Output directory cannot be inside input directory."
        )

    except ValueError:
        pass

    logger.info("=" * 65)
    logger.info("FACE + CAR DETECTION PIPELINE")
    logger.info("=" * 65)

    logger.info("Input directory: %s", input_dir)
    logger.info("Output directory: %s", output_dir)

    # Load models once.
    face_detector = load_face_detector(
        model_path=args.face_model,
        detection_size=args.face_input_size,
        confidence_threshold=args.face_threshold,
    )

    car_detector = load_car_detector(
        weights_path=args.rfdetr_weights,
    )

    # Find input images.
    image_paths = find_images(input_dir)

    if not image_paths:
        logger.warning(
            "No images found in: %s",
            input_dir,
        )
        return

    logger.info(
        "Total images found: %d",
        len(image_paths),
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary = {
        "input_directory": str(input_dir),
        "output_directory": str(output_dir),
        "face_model": str(
            Path(args.face_model).expanduser().resolve()
        ),
        "rfdetr_weights": args.rfdetr_weights,
        "face_threshold": args.face_threshold,
        "car_threshold": args.car_threshold,
        "face_input_size": args.face_input_size,
        "total_images": len(image_paths),
        "processed_images": 0,
        "failed_images": 0,
        "total_faces": 0,
        "total_cars": 0,
        "results": [],
    }

    # Process images.
    for index, image_path in enumerate(
        image_paths,
        start=1,
    ):

        relative_path = image_path.relative_to(
            input_dir
        )

        output_path = output_dir / relative_path

        logger.info(
            "[%d/%d] Processing: %s",
            index,
            len(image_paths),
            relative_path,
        )

        try:

            result = process_image(
                image_path=image_path,
                output_path=output_path,
                face_detector=face_detector,
                car_detector=car_detector,
                face_detection_size=args.face_input_size,
                face_threshold=args.face_threshold,
                car_threshold=args.car_threshold,
            )

            summary["processed_images"] += 1
            summary["total_faces"] += result["faces"]
            summary["total_cars"] += result["cars"]

            summary["results"].append(result)

            logger.info(
                "Completed | Faces: %d | Cars: %d",
                result["faces"],
                result["cars"],
            )

        except Exception as error:

            logger.exception(
                "Failed to process: %s",
                image_path,
            )

            summary["failed_images"] += 1

            summary["results"].append({
                "input": str(image_path),
                "status": "failed",
                "error": str(error),
            })

    # Save final summary.
    summary_path = (
        output_dir / "detections_summary.json"
    )

    with open(
        summary_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=4,
        )

    # Final report.
    logger.info("=" * 65)
    logger.info("PROCESSING COMPLETED")
    logger.info("=" * 65)

    logger.info(
        "Total images: %d",
        summary["total_images"],
    )

    logger.info(
        "Successfully processed: %d",
        summary["processed_images"],
    )

    logger.info(
        "Failed images: %d",
        summary["failed_images"],
    )

    logger.info(
        "Total faces detected: %d",
        summary["total_faces"],
    )

    logger.info(
        "Total cars detected: %d",
        summary["total_cars"],
    )

    logger.info(
        "Summary: %s",
        summary_path,
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        logger.warning("Processing interrupted.")
        sys.exit(130)

    except Exception:
        logger.exception("Application failed.")
        sys.exit(1)
