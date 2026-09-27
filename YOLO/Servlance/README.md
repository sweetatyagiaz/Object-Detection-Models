# YOLO26 + ByteTrack + local face recognition

## Install

```bash
pip install ultralytics insightface onnxruntime-gpu opencv-python
# no GPU available? use onnxruntime instead of onnxruntime-gpu
```

`ultralytics>=8.4.0` is required for YOLO26 support.

## 1. Enroll known people

Put a few reference photos per person into `known_faces/<name>/`, then run:

```bash
python enroll_faces.py --input known_faces --output face_db.pkl
```

This produces `face_db.pkl`, a local database of 512-d ArcFace embeddings per person.
No GPU training step needed — enrollment is just detection + embedding extraction.

## 2. Run detection + tracking + recognition

```bash
python track_recognize.py --source rtsp://<camera-ip>/stream --db face_db.pkl --weights yolo26n.pt --show
```

- `--source` accepts an RTSP URL, a video file path, or a webcam index (`0`).
- `--weights` picks the YOLO26 size: `yolo26n.pt` (fastest, edge-friendly) up to `yolo26x.pt` (most accurate).
- Drop `--show` when running headless on a server; wire the loop in `track_recognize.py` to publish
  results to Kafka/a message queue instead of `cv2.imshow`.

## How the pieces connect

- **Tracking**: `model.track(..., tracker="bytetrack.yaml", persist=True)` is the built-in
  Ultralytics call — it runs YOLO26 for detection and ByteTrack for association in one step,
  giving each person a stable `track_id` that survives brief occlusions.
- **Recognition**: for each tracked box, we crop the person region, run InsightFace's
  `buffalo_l` (SCRFD detector + ArcFace embedding) on the crop, and compare the resulting
  512-d embedding against every enrolled embedding via cosine similarity.
- **Efficiency**: recognition is skipped for tracks that are already confidently labeled, and
  only re-checked every `RECOGNITION_INTERVAL` frames otherwise — this is what makes it viable
  across many concurrent camera streams instead of running face recognition every frame.

## Scaling to many cameras

For 1000 cameras, don't run one Python process like this per camera on one machine.
Typical pattern:
- Run this pipeline per camera group on edge boxes / GPU servers (batch several streams per GPU).
- Push `track_id` + label + timestamp + camera_id events to Kafka/RabbitMQ instead of drawing
  on-screen.
- Keep `face_db.pkl` (or migrate it to Milvus/FAISS/Qdrant for larger watchlists) on a shared
  service so all edge nodes query the same identities.
- For cross-camera re-identification (same person, different camera), also store the person's
  appearance embedding (not just face) — e.g. via OSNet — since faces aren't always visible.
