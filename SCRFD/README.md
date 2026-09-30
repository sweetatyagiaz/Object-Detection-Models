# SCRFD Face Detection

Fast and accurate face detection using **SCRFD (Sample and Computation Redistribution for Face Detection)** from InsightFace.

SCRFD is a state-of-the-art face detector optimized for real-time applications, surveillance systems, access control, attendance systems, and face recognition pipelines.

---

## Features

* Fast face detection
* Multiple face detection
* 5-point facial landmarks
* CPU and GPU support
* ONNX Runtime inference
* Face alignment support
* Compatible with ArcFace, SFace, AdaFace
* Real-time video processing

---

## Pipeline

<p align="center"><img src="SCRFD - Pipeline.png"></p>

---

## Repository Structure

```text
SCRFD/
│
├── README.md
├── requirements.txt
│
├── models/
│   ├── scrfd_500m.onnx
│   ├── scrfd_1g.onnx
│   ├── scrfd_2.5g.onnx
│   └── scrfd_10g.onnx
│
├── src/
│   ├── detector.py
│   ├── align.py
│   ├── utils.py
│   └── visualization.py
│
├── examples/
│   ├── image_detection.py
│   ├── video_detection.py
│   └── webcam_detection.py
│
├── images/
│   ├── input.jpg
│   └── output.jpg
│
└── outputs/
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/your-username/SCRFD.git
cd SCRFD
```

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

Windows:

```cmd
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Requirements

```text
numpy
opencv-python
onnxruntime
insightface
```

GPU:

```bash
pip install onnxruntime-gpu
```

---

## Download Models

Official SCRFD models:

| Model      | Parameters | Speed    | Accuracy  |
| ---------- | ---------- | -------- | --------- |
| SCRFD_500M | Small      | Fastest  | Good      |
| SCRFD_1G   | Small      | Fast     | Better    |
| SCRFD_2.5G | Medium     | Fast     | Very Good |
| SCRFD_10G  | Large      | Moderate | Excellent |
| SCRFD_34G  | Very Large | Slow     | Best      |

Place downloaded ONNX files inside:

```text
models/
```

---

## Face Detection Example

```python
from insightface.app import FaceAnalysis
import cv2

app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)

image = cv2.imread("image.jpg")

faces = app.get(image)

for face in faces:
    print("BBox:", face.bbox)
    print("Landmarks:", face.kps)
```

---

## Detection Output

```python
{
    "bbox": [120, 80, 260, 240],
    "score": 0.98,
    "landmarks": [
        [150, 140],
        [220, 142],
        [185, 180],
        [160, 215],
        [210, 218]
    ]
}
```

---

## Facial Landmarks

SCRFD predicts five facial landmarks:

```text
Left Eye
Right Eye
Nose
Left Mouth Corner
Right Mouth Corner
```

These landmarks are used for face alignment before feature extraction.

---


<p align="center"><img src="SCRFD - Face Alignment.png"></p>

---

## Supported Applications

* Face Recognition
* CCTV Analytics
* Smart Surveillance
* Visitor Management
* Attendance Systems
* Access Control
* Law Enforcement
* Missing Person Search
* Face Clustering
* Face Deduplication

---

<p align="center"><img src="SCRFD Recognition Pipline.png"></p>

---

## Performance Recommendation

### Small Systems

```text
SCRFD_500M
```

### CPU Deployment

```text
SCRFD_1G
```

### Real-Time Surveillance

```text
SCRFD_2.5G
```

### Face Recognition Systems

```text
SCRFD_10G
```

### Research & Benchmarking

```text
SCRFD_34G
```

---

## Example Command

Detect faces in an image:

```bash
python examples/image_detection.py \
    --image images/input.jpg
```

Video processing:

```bash
python examples/video_detection.py \
    --video video.mp4
```

Webcam:

```bash
python examples/webcam_detection.py
```

---

## Future Enhancements

* Face Tracking
* Multi-Camera Processing
* Face Quality Assessment
* Blur Detection
* Mask Detection
* Age & Gender Estimation
* Face Recognition Integration
* FAISS Database Search
* Distributed Processing

---

## References

* InsightFace
* SCRFD: Sample and Computation Redistribution for Efficient Face Detection
* ONNX Runtime
* ArcFace
* SFace
