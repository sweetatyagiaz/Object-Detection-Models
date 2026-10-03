
from adaface import AdaFace

MODEL_PATH="../models/adaface_ir50.onnx"
DATABASE_DIR = "../datasets/dataset_deepface"
INDEX_PATH = "../datasets/fiss_indexes/face_index_adaface.bin"
MAPPING_PATH="../datasets/fiss_indexes/mapping_adaface.json"

adaface = AdaFace(
    model_path=MODEL_PATH,
    database_dir=DATABASE_DIR,
    index_path=INDEX_PATH,
    mapping_path=MAPPING_PATH
)

# Create index once
adaface.build_index()

# Search
image_path = "../datasets/extracted_faces/vimala_face_1.jpg"

results = adaface.search_face(
    image_path,
    top_k=5,
    threshold=0.5
)

for result in results:
    print(result)