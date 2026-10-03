import json
import os
import pickle

import cv2
import numpy as np


class EmbeddingGenerator:

    def __init__(
        self,
        recognizer
    ):
        self.recognizer = recognizer

    def create_embeddings(
        self,
        dataset_dir,
        output_file
    ):

        embeddings = []

        total_images = 0
        successful = 0
        failed = 0

        print("\nCreating Embeddings...\n")

        for person_folder in sorted(
            os.listdir(dataset_dir)
        ):

            person_dir = os.path.join(
                dataset_dir,
                person_folder
            )

            if not os.path.isdir(
                person_dir
            ):
                continue

            try:

                person_id = int(
                    person_folder.split(".")[0]
                )

            except Exception:

                print(
                    f"Invalid folder name: "
                    f"{person_folder}"
                )

                continue

            metadata = {}

            metadata_file = os.path.join(
                person_dir,
                "metadata.json"
            )

            if os.path.exists(
                metadata_file
            ):

                with open(
                    metadata_file,
                    "r",
                    encoding="utf-8"
                ) as fp:

                    metadata = json.load(
                        fp
                    )

            print(
                f"\nProcessing: "
                f"{person_folder}"
            )

            for filename in sorted(
                os.listdir(person_dir)
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
                    person_dir,
                    filename
                )

                image = cv2.imread(
                    image_path
                )

                if image is None:

                    failed += 1

                    print(
                        f"Cannot read: "
                        f"{image_path}"
                    )

                    continue

                try:

                    result = (
                        self.recognizer
                        .get_embedding(
                            image
                        )
                    )

                except Exception as error:

                    failed += 1

                    print(
                        f"Embedding Error: "
                        f"{filename}"
                    )

                    print(error)

                    continue

                if result is None:

                    failed += 1

                    continue

                embedding = result[
                    "embedding"
                ]

                quality = result[
                    "quality"
                ]

                embedding = np.asarray(
                    embedding,
                    dtype=np.float32
                )

                face_size = None
                dataset_quality = None

                if filename in metadata:

                    face_size = (
                        metadata[
                            filename
                        ].get(
                            "face_size"
                        )
                    )

                    dataset_quality = (
                        metadata[
                            filename
                        ].get(
                            "quality"
                        )
                    )

                embeddings.append(
                    {
                        "person_id": person_id,
                        "person_name": person_folder,
                        "image_name": filename,
                        "image_path": image_path,
                        "face_size": face_size,
                        "dataset_quality": dataset_quality,
                        "adaface_quality": float(
                            quality
                        ),
                        "embedding": embedding
                    }
                )

                successful += 1

                print(
                    f"Embedded: "
                    f"{person_folder}/"
                    f"{filename}"
                )

        output_dir = os.path.dirname(
            output_file
        )

        if output_dir:

            os.makedirs(
                output_dir,
                exist_ok=True
            )

        with open(
            output_file,
            "wb"
        ) as fp:

            pickle.dump(
                embeddings,
                fp
            )

        print("\n" + "=" * 60)

        print(
            "EMBEDDING SUMMARY"
        )

        print("=" * 60)

        print(
            f"Total Images : "
            f"{total_images}"
        )

        print(
            f"Successful   : "
            f"{successful}"
        )

        print(
            f"Failed       : "
            f"{failed}"
        )

        print(
            f"Saved File   : "
            f"{output_file}"
        )

        print("=" * 60)

        return embeddings