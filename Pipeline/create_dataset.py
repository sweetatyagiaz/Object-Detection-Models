"""
Create an annotated face + car detection dataset.

Reusable model and image-processing functions are imported from utils.py.
"""

import argparse
import logging
from pathlib import Path

from utils import (
    DEFAULT_CAR_THRESHOLD,
    DEFAULT_FACE_THRESHOLD,
    DEFAULT_SCRFD_MODEL,
    configure_logging,
    load_car_detector,
    load_face_detector,
    process_image,
)


IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp",
    ".tif", ".tiff", ".webp",
}


def create_dataset(
    input_dir,
    output_dir,
    scrfd_model=DEFAULT_SCRFD_MODEL,
    face_threshold=DEFAULT_FACE_THRESHOLD,
    car_threshold=DEFAULT_CAR_THRESHOLD,
    scrfd_device_id=-1,
    face_input_size=(640, 640),
):
    """Recursively process images and preserve their subdirectory structure."""
    logger = logging.getLogger("face-car-detection")

    input_dir = Path(input_dir).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    scrfd_model = Path(scrfd_model).expanduser().resolve()

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {input_dir}")

    if input_dir == output_dir or input_dir in output_dir.parents:
        raise ValueError(
            "Output directory must not be the input directory or a directory "
            "inside the input directory."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load each model once, not once per image.
    face_detector = load_face_detector(
        model_path=scrfd_model,
        device_id=scrfd_device_id,
        input_size=face_input_size,
    )
    car_detector = load_car_detector()

    image_files = sorted(
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )

    logger.info("Input directory: %s", input_dir)
    logger.info("Output directory: %s", output_dir)
    logger.info("Images found: %d", len(image_files))

    processed = 0
    failed = 0
    total_faces = 0
    total_cars = 0

    for image_path in image_files:
        try:
            result = process_image(
                image_path=image_path,
                input_dir=input_dir,
                output_dir=output_dir,
                face_detector=face_detector,
                car_detector=car_detector,
                face_threshold=face_threshold,
                car_threshold=car_threshold,
            )

            if result is None:
                failed += 1
                continue

            processed += 1
            total_faces += result["summary"]["faces"]
            total_cars += result["summary"]["cars"]

        except Exception:
            failed += 1
            logger.exception("Failed processing: %s", image_path)

    logger.info("=" * 60)
    logger.info("DATASET CREATION COMPLETED")
    logger.info("Images discovered: %d", len(image_files))
    logger.info("Images processed: %d", processed)
    logger.info("Images failed: %d", failed)
    logger.info("Faces detected: %d", total_faces)
    logger.info("Cars detected: %d", total_cars)
    logger.info("Output directory: %s", output_dir)
    logger.info("=" * 60)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create an annotated face + car detection dataset."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("/home/rakesh/datasets/raw_data"),
        help="Root directory containing input images.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/home/rakesh/datasets/dataset_rf_detr"),
        help="Output directory for annotated images and JSON.",
    )
    parser.add_argument(
        "--scrfd-model",
        type=Path,
        default=DEFAULT_SCRFD_MODEL,
        help="Path to the SCRFD_34G ONNX model.",
    )
    parser.add_argument(
        "--face-threshold",
        type=float,
        default=DEFAULT_FACE_THRESHOLD,
    )
    parser.add_argument(
        "--car-threshold",
        type=float,
        default=DEFAULT_CAR_THRESHOLD,
    )
    parser.add_argument(
        "--scrfd-device-id",
        type=int,
        default=-1,
        help="-1 for CPU; 0 for the first CUDA device.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    configure_logging()

    create_dataset(
        input_dir=args.input,
        output_dir=args.output,
        scrfd_model=args.scrfd_model,
        face_threshold=args.face_threshold,
        car_threshold=args.car_threshold,
        scrfd_device_id=args.scrfd_device_id,
    )


if __name__ == "__main__":
    main()
