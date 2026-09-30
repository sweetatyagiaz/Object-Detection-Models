# SFace

## Overview

SFace (Sigmoid-Constrained Hypersphere Loss) is a deep-learning face recognition model designed for generating discriminative face embeddings. It is available through OpenCV's DNN module and is commonly used together with YuNet for lightweight face recognition systems.

---

## Category

* Computer Vision
* Face Recognition
* Biometric Identification
* Face Verification

---

## Source

* Paper: SFace – Sigmoid-Constrained Hypersphere Loss
* OpenCV Zoo Implementation
* OpenCV FaceRecognizerSF API

---

## Model Details

| Parameter          | Value            |
| ------------------ | ---------------- |
| Task               | Face Recognition |
| Framework          | OpenCV DNN       |
| Input Face Size    | 112 × 112        |
| Landmark Alignment | 5-point          |
| Embedding Type     | L2 Normalized    |
| License            | Apache 2.0       |
| Deployment         | CPU / GPU        |

The model performs face alignment before feature extraction and then generates a compact embedding suitable for similarity search and face matching.

---

## Architecture

### Pipeline

<p align="center"><img src="SFace - Architecture Pipeline.png"></p>

---

## Embedding Dimension

### My Notes

Different implementations report either:

* 128-dimensional embeddings
* 512-dimensional embeddings

This depends on the implementation and exported model version being used. Before building a FAISS index, always verify using:

```python
feature = recognizer.feature(aligned_face)
print(feature.shape)
```

Use the actual output dimension from the deployed model as the FAISS dimension.

### Current Project

```text
Dimension Tested:
Date Tested:
Model File:
```

---

## Strengths

* Fast CPU inference
* Native OpenCV support
* Lightweight deployment
* Easy ONNX integration
* Good recognition accuracy
* Suitable for real-time surveillance
* No PyTorch dependency during inference
* Works well with FAISS vector search

---

## Weaknesses

* Accuracy lower than modern ArcFace variants in challenging conditions.
* Sensitive to poor face detection and alignment.
* Performance decreases for tiny faces.
* Requires high-quality enrollment images.
* Recognition quality depends heavily on detector quality.

---

## Comparison With ArcFace

| Feature            | SFace     | ArcFace   |
| ------------------ | --------- | --------- |
| Speed              | Faster    | Slower    |
| CPU Deployment     | Excellent | Good      |
| Accuracy           | Good      | Very High |
| OpenCV Integration | Native    | External  |
| Ease of Deployment | Easy      | Medium    |
| Surveillance Usage | Good      | Excellent |

---

## Recommended Use Cases

### Good For

* Home surveillance
* Small office surveillance
* Attendance systems
* Visitor management
* Embedded devices
* Edge AI deployments
* Real-time face recognition

### Not Ideal For

* Very large-scale national databases
* Extremely low-resolution faces
* Long-range surveillance cameras
* Highly unconstrained environments

---

## FAISS Notes

### Recommended Index

For small deployments:

```python
faiss.IndexFlatIP()
```

For large deployments:

```python
faiss.IndexIVFFlat()
```

### Important

Normalize embeddings before insertion:

```python
faiss.normalize_L2(embeddings)
```

Use cosine similarity matching.

---

## Threshold Notes

OpenCV examples commonly reference:

```text
Cosine Similarity Threshold ≈ 0.363
L2 Threshold ≈ 1.128
```

These values should be treated as starting points and re-tuned using project-specific data.

### My Production Threshold

```text
Date:
Dataset:
Threshold:
FAR:
FRR:
```

---

## Dataset Requirements

### Recommended

* 20–100 images per person
* Multiple poses
* Multiple expressions
* Multiple lighting conditions
* No blurry images
* No duplicate images

### Face Size

Recommended minimum:

```text
112 × 112
```

Larger faces generally improve recognition performance.

---

## Experiments

### Experiment 1

Date:

Dataset:

Result:

Observations:

Decision:

---

### Experiment 2

Date:

Dataset:

Result:

Observations:

Decision:

---

## Lessons Learned

### 2026

* Detector quality impacts recognition more than embedding model choice.
* More enrollment images improve recognition stability.
* Duplicate images do not significantly improve accuracy.
* Blurry faces create unstable embeddings.
* Alignment quality directly affects matching performance.

---

## Future Work

* Test ArcFace vs SFace on surveillance dataset.
* Benchmark FAISS Flat vs IVF.
* Test quantized models.
* Evaluate performance on 1000+ identities.
* Measure multi-camera scalability.

---

## Production Decision

### Current Status

```text
[ ] Research
[ ] Testing
[ ] Benchmarking
[ ] Production
```

### Final Decision

```text
Reason:
Date:
Approved By:
```
