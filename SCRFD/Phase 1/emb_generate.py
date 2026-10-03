from adaface_recognizer import AdaFaceRecognizer
from embedding_generator import EmbeddingGenerator

MODEL_PATH = "../../models/adaface_ir50.onnx"

recognizer = AdaFaceRecognizer(
    model_path=MODEL_PATH
)

generator = EmbeddingGenerator(
    recognizer=recognizer
)

generator.create_embeddings(
    dataset_dir="../../datasets/dataset_scrfd",
    output_file="../../datasets/embeddings/AdaFace/embeddings_scrfd.pkl"
)