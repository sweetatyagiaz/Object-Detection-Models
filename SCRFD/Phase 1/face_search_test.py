import cv2

from adaface_recognizer import (
    AdaFaceRecognizer
)

from face_searcher import (
    FaceSearcher
)

MODEL_PATH = "../../models/adaface_ir50.onnx"

recognizer = AdaFaceRecognizer(
    model_path=MODEL_PATH
)

searcher = FaceSearcher(
    recognizer=recognizer,
    index_file="../../datasets/FAISS/AdaFace/faiss.index",
    gallery_file="../../datasets/FAISS/AdaFace/gallery.pkl"
)

IMG_PATH = "../../datasets/images/Tejrit.jpg"

# Search Image
results = searcher.search_image_file(
    IMG_PATH,
    top_k=5
)

for row in results:

    print(
        f"Score : "
        f"{row['score']:.4f}"
    )

    print(
        f"ID    : "
        f"{row['person_id']}"
    )

    print(
        f"Name  : "
        f"{row['person_name']}"
    )

    print()


image = image = cv2.imread(IMG_PATH)
results = searcher.search_person(
    image=image,
    top_k=20
)

# print(results)

for result in results:

    print(
        f"ID         : {result['person_id']}"
    )

    print(
        f"Name       : {result['person_name']}"
    )

    print(
        f"Best Score : {result['best_score']}"
    )

    print(
        f"Avg Score  : {result['avg_score']}"
    )

    print(
        f"Matches    : {result['matches']}"
    )

    print()