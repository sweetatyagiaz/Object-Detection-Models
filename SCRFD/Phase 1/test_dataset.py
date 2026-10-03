from scrfd_detector import SCRFDDetector
from face_aligner import FaceAligner
from dataset_builder import DatasetBuilder

INPUT_DIR = "/home/rakesh/GitRepo/Object-Detection-Models/datasets/raw_data"
OUTPUT_DIR = "/home/rakesh/GitRepo/Object-Detection-Models/datasets/dataset_scrfd"

detector = SCRFDDetector()

aligner = FaceAligner(
    image_size=112,
    min_face_size=50
)

dataset_builder = DatasetBuilder(
    detector=detector,
    aligner=aligner
)

dataset_builder.create_dataset(
    detector=detector,
    input_dir=INPUT_DIR,
    output_dir=OUTPUT_DIR
)