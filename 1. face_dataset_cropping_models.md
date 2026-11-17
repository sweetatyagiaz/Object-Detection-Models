# Top Models for Face Dataset Cropping

* **SCRFD (`det_10g` / `det_2.5g`) — Best Overall Speed & Accuracy:** InsightFace's Sample and Computation Redistribution detector offers the strongest accuracy-to-speed trade-off across scales, handles side profiles and partial occlusions well, and exports cleanly to ONNX Runtime.
* **RetinaFace (`ResNet50`) — Best for Tiny, Distant, or Difficult Faces:** Achieves top recall on crowded scenes, small faces, and extreme angles (99.4% precision on WIDER FACE), making it ideal for offline batch dataset curation on a GPU where accuracy matters more than real-time FPS.
* **YuNet — Best for CPU-Only & Commercial Licensing:** Ultra-lightweight (~75K parameters, ~230 KB ONNX file) and built directly into OpenCV (`cv2.FaceDetectorYN`) under an Apache 2.0 / MIT-friendly license, running in milliseconds per image on CPU.
* **MediaPipe Face Detector (BlazeFace) — Best for Close-Up / Selfie Datasets:** Extremely fast on mobile or CPU for front-facing and medium-range portraits, though less accurate on small or distant faces in group shots.

## Quick Comparison

| Model | 5-Point Landmarks | Speed | Hardware Target | License / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **SCRFD (`det_10g`)** | Yes | Very Fast | GPU / CPU (ONNX) | Non-commercial research license (InsightFace) |
| **RetinaFace (`R50`)** | Yes | Moderate | GPU | Non-commercial research license (InsightFace) |
| **YuNet** | Yes | Ultra-Fast | CPU / Edge | MIT / Apache 2.0 (Commercial-safe, built into OpenCV) |
| **MediaPipe** | Yes (6-point) | Ultra-Fast | CPU / Mobile | Apache 2.0 (Best for close-up portraits) |
