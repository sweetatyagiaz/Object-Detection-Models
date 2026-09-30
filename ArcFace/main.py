
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


from utils import create_faiss_index, create_embedding_arcface, search_face

# DATABASE_DIR = "../datasets/extracted_faces_SCRFD" # currently not completed: but it will take SCRFD extracted faces
DATABASE_DIR = "../datasets/extracted_faces_datasets"
OUTPUT_DIR = "../datasets/embeddings/ArcFace"
EMBEDDINGS_FILE = OUTPUT_DIR + "/embeddings.npy"
MAPPING_FILE = OUTPUT_DIR + "/mapping.json"
INDEX_DIR = "../datasets/fiss_indexes"
INDEX_FILE = "face_index_arcface.faiss"
image_path = "../datasets/extracted_faces_SCRFD/face_1.jpg"

# create embeddings
app = create_embedding_arcface(DATABASE_DIR=DATABASE_DIR, OUTPUT_DIR=OUTPUT_DIR)

# CREATE FAISS FILE
create_faiss_index(EMBEDDINGS_FILE=EMBEDDINGS_FILE, MAPPING_FILE=MAPPING_FILE, INDEX_DIR=INDEX_DIR, 
                   INDEX_FILE=INDEX_FILE)

# search face
search_face(app=app, TOP_K=5, INDEX_FILE=INDEX_DIR + '/' + INDEX_FILE, MAPPING_FILE=MAPPING_FILE, 
            image_path=image_path)





