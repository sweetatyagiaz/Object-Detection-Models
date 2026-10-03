import os
import cv2
import json

class DatasetBuilder:

    def __init__(self, detector, aligner):
        self.detector = detector
        self.aligner = aligner

    def create_dataset(self, detector, input_dir, output_dir):
        """
        Create aligned face dataset.

        Input:
            raw_data/
            ├── Person1/
            │   ├── img1.jpg
            │   └── img2.jpg
            │
            └── Person2/
                ├── img1.jpg
                └── img2.jpg

        Output:
            aligned_data/
            ├── Person1/
            │   ├── img1.jpg
            │   ├── img2.jpg
            │   └── metadata.json
            │
            └── Person2/
                ├── img1.jpg
                ├── img2.jpg
                └── metadata.json
        """

        os.makedirs(output_dir, exist_ok=True)

        total_images = 0
        saved_images = 0
        skipped_images = 0
        no_face_images = 0
        poor_quality_images = 0

        for person_name in sorted(os.listdir(input_dir)):

            person_input_dir = os.path.join(input_dir, person_name)

            if not os.path.isdir(person_input_dir):
                continue

            print(f"\nProcessing Person: {person_name}")

            person_output_dir = os.path.join(output_dir, person_name)

            os.makedirs(person_output_dir, exist_ok=True)

            metadata = {}

            for filename in sorted(os.listdir(person_input_dir)):

                if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp")):
                    continue

                total_images += 1

                image_path = os.path.join(person_input_dir, filename)

                image = cv2.imread(image_path)

                if image is None:

                    skipped_images += 1

                    print(f"[SKIP] Cannot read: " f"{image_path}")
                    continue

                try:

                    faces = detector.detect(image)

                except Exception as error:

                    skipped_images += 1

                    print(f"[ERROR] {filename}: " f"{error}")
                    continue

                if len(faces) == 0:

                    no_face_images += 1

                    print(f"[NO FACE] {filename}")

                    continue

                # Select largest face
                face = max(
                    faces,
                    key=lambda f:
                    (f.bbox[2] - f.bbox[0]) *
                    (f.bbox[3] - f.bbox[1])
                )

                result = self.aligner.align(image=image, landmarks=face.kps, bbox=face.bbox)

                if not result["valid"]:

                    poor_quality_images += 1

                    print(f"[REJECTED] {filename} " f"({result['quality']})")

                    continue

                output_path = os.path.join(person_output_dir, filename)

                success = cv2.imwrite(output_path, result["aligned_face"])

                if not success:

                    skipped_images += 1

                    print(f"[SAVE FAILED] " f"{output_path}")

                    continue

                metadata[filename] = {"face_size": result["face_size"], "quality": result["quality"]}

                saved_images += 1

                print(f"[SAVED] {filename} " f"({result['quality']})")

            # creating metadata file
            print(f"Saving metadata file: " f"{person_output_dir}/metadata.json")
                        
            metadata_path = os.path.join(person_output_dir, "metadata.json" )
            
            with open(metadata_path, "w", encoding="utf-8") as file:
                json.dump(metadata, file, indent=4)

            print(f"Saving metadata: {metadata_path}")
            # print(metadata)

        print("\n" + "=" * 60)
        print("DATASET CREATION SUMMARY")
        print("=" * 60)

        print(
            f"Total Images      : {total_images}"
        )

        print(
            f"Saved Images      : {saved_images}"
        )

        print(
            f"No Face Images    : {no_face_images}"
        )

        print(
            f"Poor Quality      : {poor_quality_images}"
        )

        print(
            f"Skipped Images    : {skipped_images}"
        )

        print("=" * 60)