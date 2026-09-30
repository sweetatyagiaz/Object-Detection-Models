
'''
project/
│
├── database/
│   ├── 1.Rakesh_Ranjan/
│   │   ├── img1.jpg
│   │   ├── img2.jpg
│   │   └── img3.jpg
│   │
│   ├── 2.Amit_Kumar/
│   └── ...
│
├── embeddings/
│   ├── embeddings.npy
│   └── mapping.json
│
├── indexes/
│   └── face_index.faiss
│
└── generate_embeddings.py

'''


import os
import json
import cv2
import numpy as np
from tqdm import tqdm
import insightface


DATABASE_DIR = "../datasets/extracted_faces_SCRFD"
OUTPUT_DIR = "../datasets/embeddings/ArcFace"

os.makedirs(OUTPUT_DIR, exist_ok=True)

EMBEDDINGS_FILE = os.path.join(OUTPUT_DIR, "embeddings.npy")
MAPPING_FILE = os.path.join(OUTPUT_DIR, "mapping.json")


def get_person_info(folder_name):
    """
    Example:
        1.Rakesh_Ranjan

    Returns:
        person_id = 1
        person_name = Rakesh_Ranjan
    """
    try:
        person_id, person_name = folder_name.split(".", 1)
        return int(person_id), person_name
    except Exception:
        return None, folder_name


def load_arcface():
    app = insightface.app.FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )

    app.prepare(ctx_id=0)
    return app


def main():

    app = load_arcface()

    all_embeddings = []
    mapping = []

    people = sorted(os.listdir(DATABASE_DIR))

    for person_folder in tqdm(people, desc="Processing Persons"):

        person_path = os.path.join(DATABASE_DIR, person_folder)

        if not os.path.isdir(person_path):
            continue

        person_id, person_name = get_person_info(person_folder)

        for image_name in os.listdir(person_path):

            if not image_name.lower().endswith(
                (".jpg", ".jpeg", ".png", ".webp")
            ):
                continue

            image_path = os.path.join(person_path, image_name)

            try:

                image = cv2.imread(image_path)

                if image is None:
                    continue

                faces = app.get(image)

                if len(faces) == 0:
                    print(f"[NO FACE] {image_path}")
                    continue

                face = max(
                    faces,
                    key=lambda x: x.bbox[2] - x.bbox[0]
                )

                embedding = face.embedding

                embedding = embedding.astype(np.float32)

                all_embeddings.append(embedding)

                mapping.append(
                    {
                        "person_id": person_id,
                        "person_name": person_name,
                        "image_path": image_path,
                    }
                )

            except Exception as error:
                print(f"[ERROR] {image_path}: {error}")

    all_embeddings = np.array(all_embeddings)

    np.save(EMBEDDINGS_FILE, all_embeddings)

    with open(MAPPING_FILE, "w") as file:
        json.dump(mapping, file, indent=4)

    print()
    print("=" * 50)
    print(f"Embeddings : {len(all_embeddings)}")
    print(f"Saved      : {EMBEDDINGS_FILE}")
    print(f"Mapping    : {MAPPING_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    main()