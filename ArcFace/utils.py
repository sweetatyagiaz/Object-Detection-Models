
import json
import faiss
import numpy as np
import os
import cv2
from tqdm import tqdm
import insightface


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

def create_embedding_arcface(DATABASE_DIR=False, OUTPUT_DIR=False):

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    EMBEDDINGS_FILE = os.path.join(OUTPUT_DIR, "embeddings.npy")
    MAPPING_FILE = os.path.join(OUTPUT_DIR, "mapping.json")

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
    
    return app

def create_faiss_index(EMBEDDINGS_FILE=False, MAPPING_FILE=False, INDEX_DIR=False, INDEX_FILE=False):
    
    # CREATE FISS FILE
    INDEX_FILE = os.path.join(INDEX_DIR, INDEX_FILE)

    embeddings = np.load(
        EMBEDDINGS_FILE
    ).astype(np.float32)

    print(
        f"Loaded embeddings: {embeddings.shape}"
    )

    dimension = embeddings.shape[1]

    # index = faiss.IndexFlatIP(
    #     dimension
    # )
    index = faiss.IndexHNSWFlat(512, 32, faiss.METRIC_INNER_PRODUCT)

    faiss.normalize_L2(
        embeddings
    )

    index.add(
        embeddings
    )

    faiss.write_index(
        index,
        INDEX_FILE
    )

    print()
    print("=" * 50)
    print(f"Dimension : {dimension}")
    print(f"Vectors   : {index.ntotal}")
    print(f"Saved     : {INDEX_FILE}")
    print("=" * 50)

    return True

def search_face(app=False, TOP_K=5, INDEX_FILE=False, MAPPING_FILE=False, image_path=False):

    if not app:
        app = load_arcface()

    # read index & mapping file
    index = faiss.read_index(INDEX_FILE)

    with open(MAPPING_FILE) as file:
        mapping = json.load(file)

    # read image
    image = cv2.imread(image_path)

    # get face
    faces = app.get(image)

    if len(faces) == 0:
        print("No face found")
        return

    face = max(
        faces,
        key=lambda x: x.bbox[2] - x.bbox[0]
    )

    embedding = face.embedding.astype(
        np.float32
    )

    embedding = embedding.reshape(
        1,
        -1
    )

    faiss.normalize_L2(
        embedding
    )

    scores, indices = index.search(
        embedding,
        TOP_K
    )

    print("\nTop Matches:\n")

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        person = mapping[idx]

        print(
            f"Score : {score:.4f}"
        )
        print(
            f"ID    : {person['person_id']}"
        )
        print(
            f"Name  : {person['person_name']}"
        )
        print(
            f"Image : {person['image_path']}"
        )
        print("-" * 50)
    