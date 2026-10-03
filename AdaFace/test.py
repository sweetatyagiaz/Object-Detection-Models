import logging

from adaface import AdaFace

logging.basicConfig(level=logging.INFO)

MODEL_PATH = "../models/adaface_ir50.onnx"
DATABASE_DIR = "../datasets/dataset_deepface"
INDEX_PATH = "../datasets/faiss_indexes/face_index_adaface.bin"
MAPPING_PATH = "../datasets/faiss_indexes/mapping_adaface.json"

adaface = AdaFace(
    model_path=MODEL_PATH,
    database_dir=DATABASE_DIR,
    index_path=INDEX_PATH,
    mapping_path=MAPPING_PATH,
    # min_quality=None,   # set after inspecting the quality values in the mapping json
)

# Rebuild whenever the dataset (or preprocessing) changes.
# The old index/mapping files are NOT compatible: delete them or just rebuild.
adaface.build_index()

# Replace 0.4 with the threshold printed by calibrate.py
THRESHOLD = 0.4

image_path = "../datasets/extracted_faces/vimala_face_1.jpg"
results = adaface.search_face(image_path, top_k=5, threshold=THRESHOLD)

if not results:
    print("No match above threshold (or no face found in the query image).")
for r in results:
    print(r)
