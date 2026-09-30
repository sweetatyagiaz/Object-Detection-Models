# AdaFace Face Recognition

AdaFace is a state-of-the-art face recognition model designed to improve recognition performance on real-world images with varying quality levels. Unlike traditional face recognition models that use a fixed margin during training, AdaFace adapts the margin according to image quality, making it highly effective for surveillance, CCTV, mobile, and unconstrained face recognition applications.

---

## Features

- Quality-Adaptive Face Recognition
- Robust to Blur and Motion Artifacts
- Effective on Low-Resolution Faces
- Better Performance on CCTV Images
- 512-Dimensional Face Embeddings
- FAISS Integration for Large-Scale Search
- Supports Real-Time Recognition Pipelines
- Compatible with SCRFD, RetinaFace, and YuNet Detectors

---

## Architecture

<p align="center"><img src="AdaFace-Architecture Pipeline.png"></p>

---

## Why AdaFace?

Traditional face recognition models assume that all images have similar quality.

Real-world deployments often involve:

- Low-resolution CCTV footage
- Motion blur
- Poor illumination
- Occlusions
- Partial faces
- Non-frontal views

AdaFace dynamically adjusts its training margin according to image quality, improving recognition accuracy in these challenging scenarios.

---

## Comparison

| Feature | ArcFace | AdaFace |
|----------|----------|----------|
| High Quality Images | Excellent | Excellent |
| Low Resolution Images | Good | Excellent |
| Motion Blur | Good | Excellent |
| CCTV Footage | Good | Excellent |
| Surveillance Systems | Good | Excellent |
| Real-world Robustness | Good | Excellent |

---

## Recommended Production Pipeline

```text
Video Stream
      │
      ▼
SCRFD Face Detection
      │
      ▼
Face Alignment
      │
      ▼
AdaFace Embedding Extraction
      │
      ▼
FAISS Vector Search
      │
      ▼
Person Identification
```
<p align="center"><img src="AdaFace-Production Stack.png"></p>

---

## Project Structure

```text
AdaFace/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── database/
│
├── models/
│   ├── adaface_ir50.onnx
│   └── adaface_ir100.onnx
│
├── src/
│   ├── detectors/
│   ├── aligners/
│   ├── embeddings/
│   ├── faiss/
│   └── utils/
│
├── examples/
│   ├── extract_embedding.py
│   ├── create_index.py
│   └── search_face.py
│
├── reports/
│
├── requirements.txt
│
└── README.md
```

---

## Dataset Structure

Recommended format:

```text
database/
│
├── 1.Rakesh_Ranjan/
│   ├── img1.jpg
│   ├── img2.jpg
│   └── img3.jpg
│
├── 2.Sunny_Singh/
│   ├── img1.jpg
│   ├── img2.jpg
│   └── img3.jpg
│
└── 3.Ajay_Kumar/
    ├── img1.jpg
    ├── img2.jpg
    └── img3.jpg
```

Folder naming convention:

```text
<ID>.<FirstName>_<LastName>
```

Example:

```text
1.Rakesh_Ranjan
```

---

## Installation

Clone repository:

```bash
git clone https://github.com/your-org/AdaFace.git
cd AdaFace
```

Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Generate Face Embeddings

```bash
python examples/extract_embedding.py \
    --image data/sample.jpg
```

Output:

```text
Embedding Shape: (512,)
```

---

## Create FAISS Index

```bash
python examples/create_index.py \
    --database database/
```

Output:

```text
Total Persons : 1000
Total Images  : 500000
Index Created Successfully
```

---

## Search Face

```bash
python examples/search_face.py \
    --image query.jpg
```

Example Output:

```text
Score : 0.92
ID    : 1
Name  : Rakesh Ranjan
```

---

## Recommended Thresholds

### Cosine Similarity

| Similarity | Interpretation |
|------------|----------------|
| > 0.80 | Same Person |
| 0.70 - 0.80 | Possible Match |
| 0.60 - 0.70 | Weak Match |
| < 0.60 | Different Person |

Thresholds should be calibrated using your dataset.

---

## FAISS Configuration

### Exact Search

```python
index = faiss.IndexFlatIP(512)
```

Advantages:

- Highest accuracy
- No approximation

Disadvantages:

- Slower on very large datasets

---

### HNSW Search

```python
index = faiss.IndexHNSWFlat(
    512,
    32
)
```

Advantages:

- Fast search
- Large-scale deployment
- Suitable for millions of embeddings

Disadvantages:

- Approximate nearest neighbors

---

## Best Practices

### Face Size

Recommended minimum:

```text
112 × 112 pixels
```

Ideal:

```text
160 × 160 pixels or larger
```

---

### Face Pose

Recommended:

```text
Yaw < ±30°
Pitch < ±20°
Roll < ±20°
```

---

### Image Quality

Avoid:

- Heavy blur
- Extreme shadows
- Overexposure
- Severe occlusion

---

## Performance Considerations

For Surveillance Systems:

```text
SCRFD
   +
AdaFace
   +
FAISS HNSW
```

provides an excellent balance between:

- Accuracy
- Speed
- Scalability

and can support large multi-camera deployments.

---

## References

### Paper

AdaFace: Quality Adaptive Margin for Face Recognition

```text
https://arxiv.org/abs/2204.00964
```

### Official Repository

```text
https://github.com/mk-minchul/AdaFace
```

---

## License

Refer to the original AdaFace repository for licensing information.

---

## Author

Face Recognition Research & Deployment Notes

Focused on:

- Surveillance Analytics
- CCTV Recognition
- Large Scale FAISS Search
- Real-Time Face Identification
- Multi-Camera Monitoring Systems
```

You can save this directly as `README.md` in your `AdaFace` GitHub repository.