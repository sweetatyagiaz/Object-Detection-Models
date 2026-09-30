
#!/usr/bin/env python3

"""
create_scrfd_dataset.py

Create an aligned face dataset using SCRFD.

Input:
    ../datasets/raw_data/

Output:
    ../datasets/database_scrfd/

Directory Structure:

datasets/
├── raw_data/
│   ├── 1.Rakesh_Ranjan/
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   └── ...
│   │
│   ├── 2.Nivan_Tyagi/
│   │   ├── image1.jpg
│   │   └── ...
│   │
│   └── ...
│
└── database_scrfd/
    ├── 1.Rakesh_Ranjan/
    │   ├── image1.jpg
    │   ├── image2.jpg
    │   └── ...
    │
    ├── 2.Nivan_Tyagi/
    │   ├── image1.jpg
    │   └── ...
    │
    └── ...

Installation:
    pip install insightface onnxruntime opencv-python tqdm

GPU:
    pip install onnxruntime-gpu
"""


from pathlib import Path

import cv2
from tqdm import tqdm

from insightface.app import FaceAnalysis
from insightface.utils import face_align


# =============================================================================
# CONFIGURATION
# =============================================================================

DATABASE_PATH = "../datasets/raw_data"

OUTPUT_DATABASE_NAME = "database_scrfd"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


# Quality Filters

MIN_CONFIDENCE = 0.80
MIN_FACE_WIDTH = 100
MIN_FACE_HEIGHT = 100
MIN_BLUR_SCORE = 120

# For test
MIN_CONFIDENCE = 0.50
MIN_FACE_WIDTH = 50
MIN_FACE_HEIGHT = 50
MIN_BLUR_SCORE = 50


# =============================================================================
# IMAGE QUALITY FUNCTIONS
# =============================================================================

def calculate_blur_score(image):
    """
    Variance of Laplacian.
    Higher score = sharper image.
    """
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    return cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()


def get_largest_face(faces):
    """
    Return the largest detected face.
    """

    if not faces:
        return None

    return max(
        faces,
        key=lambda face: (
            (face.bbox[2] - face.bbox[0])
            * (face.bbox[3] - face.bbox[1])
        )
    )


def validate_face(face, image):
    """
    Validate face quality.
    """

    if face.det_score < MIN_CONFIDENCE:
        return False, "LOW_CONFIDENCE"

    x1, y1, x2, y2 = face.bbox.astype(int)

    face_width = x2 - x1
    face_height = y2 - y1

    if face_width < MIN_FACE_WIDTH:
        return False, "FACE_TOO_SMALL"

    if face_height < MIN_FACE_HEIGHT:
        return False, "FACE_TOO_SMALL"

    face_crop = image[
        max(0, y1):min(image.shape[0], y2),
        max(0, x1):min(image.shape[1], x2)
    ]

    if face_crop.size == 0:
        return False, "INVALID_CROP"

    blur_score = calculate_blur_score(
        face_crop
    )

    if blur_score < MIN_BLUR_SCORE:
        return False, "BLURRY_FACE"

    return True, "VALID"


# =============================================================================
# PROCESS IMAGE
# =============================================================================

def process_image(
    image_path,
    output_path,
    detector
):
    """
    Detect, validate, align and save face.
    """

    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        return False, "READ_ERROR"

    try:

        faces = detector.get(image)

        if len(faces) == 0:
            return False, "NO_FACE"

        face = get_largest_face(
            faces
        )

        is_valid, reason = validate_face(
            face,
            image
        )

        if not is_valid:
            return False, reason

        aligned_face = face_align.norm_crop(
            image,
            landmark=face.kps,
            image_size=112
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        cv2.imwrite(
            str(output_path),
            aligned_face
        )

        return True, "SUCCESS"

    except Exception as exception:

        return (
            False,
            f"ERROR: {exception}"
        )


# =============================================================================
# MAIN
# =============================================================================

def create_scrfd_database(
    database_path
):

    database_path = Path(
        database_path
    )

    if not database_path.exists():

        raise FileNotFoundError(
            f"Dataset not found: "
            f"{database_path}"
        )

    output_database = (
        database_path.parent
        / OUTPUT_DATABASE_NAME
    )

    print("\n" + "=" * 80)
    print("SCRFD DATASET CREATOR")
    print("=" * 80)
    print(
        f"Input Dataset : "
        f"{database_path.resolve()}"
    )
    print(
        f"Output Dataset: "
        f"{output_database.resolve()}"
    )
    print("=" * 80)

    # -------------------------------------------------------------------------
    # SCRFD Initialization
    # -------------------------------------------------------------------------

    detector = FaceAnalysis(
        name="buffalo_l",
        providers=[
            "CPUExecutionProvider"
        ]

        # GPU:
        # providers=[
        #     "CUDAExecutionProvider"
        # ]
    )

    detector.prepare(
        ctx_id=0,
        det_size=(640, 640)
    )

    total_images = 0
    processed_images = 0
    failed_images = 0

    skip_stats = {}

    person_directories = sorted(
        [
            directory
            for directory
            in database_path.iterdir()
            if directory.is_dir()
        ]
    )

    print(
        f"\nFound "
        f"{len(person_directories)} "
        f"person folders.\n"
    )

    for person_directory in tqdm(
        person_directories,
        desc="Processing Persons"
    ):

        output_person_directory = (
            output_database
            / person_directory.name
        )

        image_files = sorted(
            [
                file
                for file
                in person_directory.iterdir()
                if (
                    file.is_file()
                    and file.suffix.lower()
                    in SUPPORTED_EXTENSIONS
                )
            ]
        )

        for image_file in image_files:

            total_images += 1

            output_file = (
                output_person_directory
                / image_file.name
            )

            success, reason = process_image(
                image_file,
                output_file,
                detector
            )

            if success:

                processed_images += 1

            else:

                failed_images += 1

                skip_stats[reason] = (
                    skip_stats.get(
                        reason,
                        0
                    ) + 1
                )

    print("\n" + "=" * 80)
    print("PROCESSING COMPLETED")
    print("=" * 80)

    print(
        f"Total Images      : "
        f"{total_images}"
    )

    print(
        f"Processed Images  : "
        f"{processed_images}"
    )

    print(
        f"Failed Images     : "
        f"{failed_images}"
    )

    print(
        f"Output Directory  : "
        f"{output_database}"
    )

    print("\nSkip Statistics")

    for reason, count in sorted(
        skip_stats.items()
    ):
        print(
            f"{reason:20s} : "
            f"{count}"
        )

    print("=" * 80)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":

    create_scrfd_database(
        DATABASE_PATH
    )