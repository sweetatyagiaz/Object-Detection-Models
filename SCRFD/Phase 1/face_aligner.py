import cv2, os

from insightface.utils import face_align


class FaceAligner:

    QUALITY_POOR = "POOR"
    QUALITY_ACCEPTABLE = "ACCEPTABLE"
    QUALITY_GOOD = "GOOD"
    QUALITY_EXCELLENT = "EXCELLENT"

    def __init__(
        self,
        image_size=112,
        min_face_size=50
    ):
        self.image_size = image_size
        self.min_face_size = min_face_size

    def get_face_size(
        self,
        bbox
    ):
        x1, y1, x2, y2 = map(int, bbox)

        width = x2 - x1
        height = y2 - y1

        return min(width, height)

    def get_quality(
        self,
        face_size
    ):

        if face_size >= 100:
            return self.QUALITY_EXCELLENT

        elif face_size >= 80:
            return self.QUALITY_GOOD

        elif face_size >= 50:
            return self.QUALITY_ACCEPTABLE

        return self.QUALITY_POOR

    def is_valid_face(
        self,
        bbox
    ):

        face_size = self.get_face_size(
            bbox
        )

        return face_size >= self.min_face_size

    def align(
        self,
        image,
        landmarks,
        bbox=None
    ):
        """
        Returns:
        {
            "aligned_face": ndarray,
            "face_size": int,
            "quality": str,
            "valid": bool
        }
        """

        if bbox is None:
            raise ValueError(
                "bbox is required"
            )

        face_size = self.get_face_size(
            bbox
        )

        quality = self.get_quality(
            face_size
        )

        valid = face_size >= self.min_face_size

        if not valid:
            return {
                "aligned_face": None,
                "face_size": face_size,
                "quality": quality,
                "valid": False
            }

        aligned_face = face_align.norm_crop(
            image,
            landmarks,
            image_size=self.image_size
        )

        return {
            "aligned_face": aligned_face,
            "face_size": face_size,
            "quality": quality,
            "valid": True
        }

    def create_dataset(
        self,
        detector,
        input_dir,
        output_dir
    ):
        """
        Create aligned face dataset while preserving
        the original folder structure.

        Parameters
        ----------
        detector : SCRFDDetector
        input_dir : str
            Raw dataset directory

        output_dir : str
            Aligned dataset directory
        """

        total_images = 0
        saved_images = 0
        skipped_images = 0

        for person_name in sorted(os.listdir(input_dir)):

            person_input_dir = os.path.join(
                input_dir,
                person_name
            )

            if not os.path.isdir(person_input_dir):
                continue

            person_output_dir = os.path.join(
                output_dir,
                person_name
            )

            os.makedirs(
                person_output_dir,
                exist_ok=True
            )

            print(f"\nProcessing: {person_name}")

            for filename in sorted(
                os.listdir(person_input_dir)
            ):

                if not filename.lower().endswith(
                    (
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".bmp",
                        ".webp"
                    )
                ):
                    continue

                total_images += 1

                image_path = os.path.join(
                    person_input_dir,
                    filename
                )

                image = cv2.imread(
                    image_path
                )

                if image is None:

                    skipped_images += 1
                    print(
                        f"Cannot read: {image_path}"
                    )
                    continue

                faces = detector.detect(
                    image
                )

                if len(faces) == 0:

                    skipped_images += 1
                    print(
                        f"No face: {image_path}"
                    )
                    continue

                # Use largest face
                face = max(
                    faces,
                    key=lambda f:
                    (f.bbox[2] - f.bbox[0]) *
                    (f.bbox[3] - f.bbox[1])
                )

                result = self.align(
                    image=image,
                    landmarks=face.kps,
                    bbox=face.bbox
                )

                if not result["valid"]:

                    skipped_images += 1

                    print(
                        f"Rejected ({result['quality']}): "
                        f"{image_path}"
                    )

                    continue

                output_path = os.path.join(
                    person_output_dir,
                    filename
                )

                cv2.imwrite(
                    output_path,
                    result["aligned_face"]
                )

                saved_images += 1

                print(
                    f"Saved: {output_path} "
                    f"[{result['quality']}]"
                )

        print("\n====================")
        print("Dataset Summary")
        print("====================")
        print(f"Total   : {total_images}")
        print(f"Saved   : {saved_images}")
        print(f"Skipped : {skipped_images}")