
from pathlib import Path
from retinaface import RetinaFace
import cv2
import os
from pathlib import Path
import numpy as np
from insightface.app import FaceAnalysis
import faiss



def extract_faces(images_folder=False, output_folder=False):
    '''
    For Face extraction from image folder
    '''
    for image_file in Path(images_folder).glob("*"):
        if image_file.suffix.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
            continue

        try:
            faces = RetinaFace.extract_faces(
                img_path=str(image_file),
                align=True
            )

            for idx, face in enumerate(faces):
                face = cv2.cvtColor(face, cv2.COLOR_RGB2BGR)

                filename = f"{image_file.stem}_face_{idx+1}.jpg"
                cv2.imwrite(
                    os.path.join(output_folder, filename),
                    face
                )

            print(f"{image_file.name}: {len(faces)} faces")

        except Exception as e:
            print(f"Error: {image_file.name} -> {e}")

    return True

def calculate_face_size(file_path=False):
    # image = cv2.imread("Datasets/group_photo.jpg")

    if not file_path:
        return False
    
    image = cv2.imread(file_path)

    faces = RetinaFace.detect_faces(image)

    print(f"File: {file_path}")
    
    for face_id, face_data in faces.items():
        x1, y1, x2, y2 = face_data["facial_area"]

        width = x2 - x1
        height = y2 - y1

        print(f"Face Size: {width} x {height}")

def check_path(path=False):
    path_obj = Path(path)

    if path_obj.is_dir():
        # print("It is a directory path.")
        return 2
    elif path_obj.is_file():
        # print("It is a full file path.")
        return 1
    else:
        # print("The path does not exist.")
        return 0

def create_embedding_image(app=False, save_emb=True, image_file_path=False, embeddings_dir=False):
    image = cv2.imread(str(image_file_path))
    
    faces = app.get(image)

    if not faces:
        return False

    embedding = faces[0].embedding

    if save_emb:
        np.save(embeddings_dir / f"{image_file_path.stem}.npy", embedding)
        print(f"Saved {image_file_path.stem}.npy")

    return embedding

def create_embeddings(save_emb=True, faces_dir=False, embeddings_dir=False):
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])

    app.prepare(ctx_id=0)

    faces_dir = Path(faces_dir)
    embeddings_dir = Path(embeddings_dir)

    embeddings_dir.mkdir(exist_ok=True)

    temp = check_path(faces_dir)

    if temp==1:
        embedding = create_embedding_image(app=app, save_emb=save_emb, image_file_path=faces_dir, embeddings_dir=embeddings_dir)
    elif temp==2:
        for image_file in faces_dir.glob("*.jpg"):
            embedding = create_embedding_image(app=app, save_emb=save_emb, image_file_path=image_file, 
                                               embeddings_dir=embeddings_dir)
    else:
        embedding = False

    return embedding

def compare_faces(face_emb1=False, face_emb2=False):
    if isinstance(face_emb1, str):
        face_emb1 = np.load(face_emb1)
    if isinstance(face_emb2, str):
        face_emb2 = np.load(face_emb2)
    
    # Cosine Similarity
    similarity = np.dot(
        face_emb1 / np.linalg.norm(face_emb1),
        face_emb2 / np.linalg.norm(face_emb2)
    )

    print(f"Similarity: {similarity:.4f}")

    if similarity > 0.5:
        print("Same Person")
        return True
    else:
        print("Different Person")
        return False

def create_faiss_index(DIMENSION = 512):
    # Create a FAISS Index
    # Cosine similarity requires normalized vectors
    index = faiss.IndexFlatIP(DIMENSION)

    print(index.ntotal)

    return index

def load_embedding(file_path=False):
    embedding = np.array([
            np.load(file_path),
        ], dtype=np.float32)
    
    # Normalize
    faiss.normalize_L2(embedding)

    return embedding

def add_embeddings(faiss_index=False, file_path=False):    
    embedding = load_embedding(file_path=file_path)

    # index.add(embedding)
    faiss_index.add(embedding)

    return True

def search_face(threshold=0.6, faiss_index=False, search_emb_path=False, search_img_path=False, embeddings_dir=False):
    if search_img_path:
        # query = create_embedding(file_path=search_img_path)
        # query = create_embedding_image(save_emb=False, faces_dir=search_img_path, embeddings_dir=embeddings_dir)
        query = create_embeddings(save_emb=False, faces_dir=search_img_path, embeddings_dir=embeddings_dir)
        # query = np.array(
        #             create_embeddings(save_emb=True, faces_dir=search_img_path, embeddings_dir=embeddings_dir),
        #             dtype=np.float32
        #             )
        query = query[np.newaxis, :]
        faiss.normalize_L2(query)
    else:
        query = np.array(
            load_embedding(file_path=search_emb_path),
            dtype=np.float32
            )
        # query = np.array(
        #     [search_emb_path],
        #     dtype=np.float32
        # )

        faiss.normalize_L2(query)

    distances, indices = faiss_index.search(
        query,
        5
    )

    score = float(distances[0][0])
    idx = int(indices[0][0])

    if score >= threshold:
        return indices, distances

    return None, distances

def faiss_load_save(option_save=False, faiss_index=False, file_path=False):
    if option_save:
        faiss.write_index(faiss_index, file_path)
    else:
        faiss_index = faiss.read_index(file_path)

        return faiss_index

