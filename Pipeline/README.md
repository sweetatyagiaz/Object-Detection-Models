# SCRFD + RF-DETR Dataset Creation Pipeline

This project creates an image dataset containing **face** and **car**
detections using:

-   **SCRFD** for face detection.
-   **RF-DETR Small** for car detection.
-   **OpenCV** for image loading, annotation, and saving.
-   **JSON** files for structured detection results.

The code is split into reusable utilities and a dataset-generation
script.

## Project structure

``` text
RF-DETR/
├── utils.py
└── create_dataset.py
```

### `utils.py`

Contains reusable model and image-processing functions:

  Function                 Responsibility
  ------------------------ ----------------------------------------
  `configure_logging()`    Configure application logging
  `load_face_detector()`   Load the SCRFD ONNX face detector
  `load_car_detector()`    Load the RF-DETR Small model
  `detect_faces()`         Detect faces in an OpenCV image
  `get_class_name()`       Resolve RF-DETR class IDs to labels
  `detect_cars()`          Detect and retain car predictions
  `annotate_image()`       Draw detection boxes and labels
  `process_image()`        Process one image and save its outputs

You can import these functions from other Python scripts:

``` python
from utils import (
    load_face_detector,
    load_car_detector,
    detect_faces,
    detect_cars,
    annotate_image,
)
```

### `create_dataset.py`

Contains the dataset-generation workflow:

-   Recursively discovers supported image files.
-   Loads both models once before processing the dataset.
-   Calls the reusable functions from `utils.py`.
-   Preserves the input directory structure in the output.
-   Saves annotated images and JSON detection files.
-   Reports processing totals and failures.

## Requirements

Use the project's Python virtual environment and install the
dependencies:

``` bash
source ~/venv_detection/bin/activate

pip install opencv-python pillow numpy insightface onnxruntime
```

RF-DETR must also be installed in the environment. If it is not already
installed:

``` bash
pip install rfdetr
```

## Model configuration

The default SCRFD model path in `utils.py` is:

``` text
/home/rakesh/AI_Models/scrfd_34g.onnx
```

The model file must be a valid SCRFD ONNX model compatible with the
InsightFace SCRFD loader. Make sure the file really contains the
SCRFD_34G model; do not substitute `det_10g.onnx` from the `buffalo_l`
pack and label it as SCRFD_34G.

The car detector is initialized using:

``` python
RFDETRSmall()
```

## Default dataset paths

`create_dataset.py` defaults to:

  Setting                     Default
  --------------------------- -----------------------------------------
  Input directory             `/home/rakesh/datasets/raw_data`
  Output directory            `/home/rakesh/datasets/dataset_rf_detr`
  SCRFD model                 `/home/rakesh/AI_Models/scrfd_34g.onnx`
  Face confidence threshold   `0.40`
  Car confidence threshold    `0.45`
  SCRFD device ID             `-1` (CPU)

The supported image extensions are `.jpg`, `.jpeg`, `.png`, `.bmp`,
`.tif`, `.tiff`, and `.webp`.

## Run the dataset creation script

From the project directory:

``` bash
cd ~/GitRepo/Object-Detection-Models/RF-DETR
source ~/venv_detection/bin/activate

python create_dataset.py
```

### Override paths and thresholds

``` bash
python create_dataset.py \
    --input /home/rakesh/datasets/raw_data \
    --output /home/rakesh/datasets/dataset_rf_detr \
    --scrfd-model /home/rakesh/AI_Models/scrfd_34g.onnx \
    --face-threshold 0.40 \
    --car-threshold 0.45 \
    --scrfd-device-id -1
```

Use `--scrfd-device-id 0` to select the first CUDA device if the
installed ONNX Runtime and InsightFace environment support it.

## Output structure

The output mirrors the input directory structure. For example:

``` text
raw_data/
├── group_a/
│   ├── image001.jpg
│   └── image002.png
└── group_b/
    └── image003.jpg
```

Produces:

``` text
dataset_rf_detr/
├── group_a/
│   ├── image001.jpg
│   ├── image001.json
│   ├── image002.png
│   └── image002.json
└── group_b/
    ├── image003.jpg
    └── image003.json
```

The image files in the output are annotated copies. The original input
images are not modified.

## JSON format

Each image has a corresponding JSON file:

``` json
{
    "image": "group_a/image001.jpg",
    "image_width": 1920,
    "image_height": 1080,
    "summary": {
        "faces": 2,
        "cars": 1,
        "total_objects": 3
    },
    "detections": [
        {
            "class": "face",
            "confidence": 0.97,
            "bbox": [120.5, 80.2, 210.4, 190.8]
        },
        {
            "class": "car",
            "confidence": 0.91,
            "bbox": [600.0, 350.0, 1100.0, 800.0]
        }
    ]
}
```

Bounding boxes use the `[x1, y1, x2, y2]` format in pixel coordinates,
measured from the top-left corner of the image.

## Reusing the utilities

The utilities can be used independently of dataset creation:

``` python
import cv2

from utils import (
    load_face_detector,
    load_car_detector,
    detect_faces,
    detect_cars,
    annotate_image,
)

face_detector = load_face_detector()
car_detector = load_car_detector()

image = cv2.imread("/path/to/image.jpg")
if image is None:
    raise FileNotFoundError("Image could not be loaded")

faces = detect_faces(image, face_detector, confidence_threshold=0.40)
cars = detect_cars(image, car_detector, confidence_threshold=0.45)

detections = faces + cars
annotated = annotate_image(image, detections)

cv2.imwrite("annotated.jpg", annotated)
```

## Important notes

1.  **Model identity:** The configured SCRFD ONNX file must actually be
    the converted SCRFD_34G model. The filename alone does not establish
    the model architecture.
2.  **RF-DETR class labels:** Car filtering depends on the installed
    RF-DETR model exposing class names that include `car`.
3.  **Threshold tuning:** Lower confidence thresholds may increase
    recall but can also increase false positives. Evaluate thresholds on
    a representative, manually reviewed sample.
4.  **GPU support:** The SCRFD device ID and RF-DETR device selection
    are separate concerns. Confirm that each model is using the intended
    execution device.
5.  **Licensing:** Check the applicable pretrained-weight and software
    licenses before commercial use.

## Troubleshooting

### `SCRFD.detect() got an unexpected keyword argument 'thresh'`

The InsightFace SCRFD API used by this project expects the threshold as
a positional argument. `utils.py` calls:

``` python
faces, _ = face_detector.detect(
    image,
    confidence_threshold,
    max_num=max_num,
)
```

Do not change this to `thresh=confidence_threshold` unless your
installed SCRFD implementation explicitly supports that keyword.

### SCRFD model not found

Check the configured path:

``` bash
ls -lh /home/rakesh/AI_Models/scrfd_34g.onnx
```

Update the path using `--scrfd-model` or change `DEFAULT_SCRFD_MODEL` in
`utils.py`.

### Images are skipped

Check that the files use one of the supported extensions and that OpenCV
can read them. Unreadable images are logged and counted as failed.

------------------------------------------------------------------------

**Entry point:** `create_dataset.py`\
**Reusable library:** `utils.py`
