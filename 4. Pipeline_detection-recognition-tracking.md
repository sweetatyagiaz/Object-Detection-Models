# High-Throughput Person Detection, Recognition & Tracking Pipeline (25–100 Cameras)

## 1. Overview
When scaling a surveillance pipeline to **25–100 IP cameras**, running full facial recognition on every frame will saturate GPU compute. Instead, the optimal architecture follows a **Detection → Tracking → Conditional Recognition** flow:

1. **Detection** locates people across batched GPU frames.
2. **Tracking** assigns a lightweight temporary `track_id` immediately on every frame.
3. **Conditional Recognition** resolves the `track_id` into a real identity once, caching the result in Redis so the tracker carries the identity forward without redundant inference.

---

## 2. Recommended Model Stack (Apache 2.0 & High-Accuracy Options)

| Pipeline Stage | Recommended Models | Role & Why It Fits 25–100 Cameras |
| :--- | :--- | :--- |
| **Person & Object Detection** | **RF-DETR** or **RT-DETRv2** (TensorRT FP16/INT8) | High accuracy on small/occluded targets, eliminates NMS bottlenecks, and uses an **Apache 2.0 license**. |
| **Multi-Object Tracking** | **NVIDIA NvDCF** (DeepStream) or **ByteTrack** | Maintains persistent IDs across frames with minimal CPU overhead so each person is recognized once per entry. |
| **Face Detection & Alignment** | **SCRFD** (`scrfd_10g` / `scrfd_34g` ONNX) or **YuNet** | Fast, accurate facial landmark extraction on entry/gate feeds prior to embedding extraction. |
| **Person Recognition** | **ArcFace (`w600k_r50`)** or **AdaFace (`ir50`)** + **FAISS** | Extracts 512-d face embeddings and matches against family, staff, and visitor vectors in <1 ms via **FAISS**. |

---

## 3. Step-by-Step Pipeline Data Flow

### Stage 1: Batched Person Detection (`RF-DETR` / `RT-DETRv2`)
* Decode RTSP sub-streams on GPU hardware (**NVDEC**) and group frames into batches of **16–32**.
* Run **RF-DETR** or **RT-DETRv2** (TensorRT FP16/INT8) to extract person bounding boxes with zero Non-Maximum Suppression (NMS) latency.

### Stage 2: Fast Multi-Object Tracking (`NvDCF` / `ByteTrack`)
* Pass detected bounding boxes into **NvDCF** or **ByteTrack** to assign a persistent `track_id` (e.g., `Track #104`) on every frame.
* Query **Redis** to check whether `Track #104` already has a verified identity attached.

### Stage 3: Conditional Face Detection & Recognition (`SCRFD` + `ArcFace`/`AdaFace`)
* **If `Track #104` is unresolved**, crop the upper body/head region and run **SCRFD** (`scrfd_10g`) to detect and align facial landmarks.
* Pass the aligned `112x112` face crop to **ArcFace (`w600k_r50`)** or **AdaFace (`ir50`)** to extract a 512-dimensional vector.
* Query **FAISS** via cosine similarity against enrolled embeddings.

### Stage 4: Identity Binding & Propagation
* Save the resolved match (e.g., `Track #104 → "Rahul (0.78)"` or `"Unknown"`) in **Redis** with a Time-To-Live (TTL).
* On subsequent frames, the tracker keeps following `Track #104` with their name attached, skipping **Stage 3** until the person exits the scene or the TTL expires.

---

## 4. Reference Python / TensorRT Worker Implementation

```python
import redis
import faiss
import numpy as np

# Connect to Redis for track_id -> identity caching
cache = redis.Redis(host="localhost", port=6379, decode_responses=True)

def process_batched_frames(
    camera_id,
    frame,
    detector,
    tracker,
    face_detector,
    recognizer,
    faiss_index,
    id_map,
    similarity_threshold=0.60
):
    # 1. PERSON DETECTION (RF-DETR / RT-DETRv2 TensorRT)
    person_boxes = detector.infer(frame)  # Returns [x1, y1, x2, y2, conf]

    # 2. MULTI-OBJECT TRACKING (ByteTrack / NvDCF)
    tracks = tracker.update(person_boxes)  # Returns [x1, y1, x2, y2, track_id]

    results = []
    for x1, y1, x2, y2, track_id in tracks:
        cache_key = f"cam:{camera_id}:track:{track_id}"
        identity = cache.get(cache_key)

        # 3. CONDITIONAL RECOGNITION (Only run if track_id is not yet identified)
        if identity is None:
            person_crop = frame[int(y1):int(y2), int(x1):int(x2)]
            
            # Detect & align face using SCRFD
            aligned_face = face_detector.detect_and_align(person_crop)
            
            if aligned_face is not None:
                # Extract 512-d embedding (ArcFace / AdaFace)
                embedding = recognizer.get_embedding(aligned_face).astype("float32")
                faiss.normalize_L2(embedding)

                # Search FAISS index
                scores, indices = faiss_index.search(embedding, k=1)
                best_score = float(scores[0][0])
                best_idx = int(indices[0][0])

                if best_score >= similarity_threshold:
                    identity = f"{id_map[best_idx]} ({best_score:.2f})"
                    # Cache verified identity for 30 seconds to avoid redundant inference
                    cache.setex(cache_key, 30, identity)
                else:
                    identity = "Unknown"
                    # Short 2-second retry window in case face angle improves
                    cache.setex(cache_key, 2, identity)
            else:
                identity = "Scanning..."

        results.append({
            "track_id": int(track_id),
            "bbox": [float(x1), float(y1), float(x2), float(y2)],
            "identity": identity
        })

    return results
```

---

## 5. Key Scaling Advantages for 25–100 Cameras

* **Eliminates Redundant GPU Load:** Caching `track_id → identity` in Redis reduces **SCRFD + ArcFace** inference calls by over **90%** when people stand or walk through monitored zones.
* **Handles Side Profiles Automatically:** If someone enters facing away (`Scanning...`), the short 2-second cache window re-triggers recognition as soon as they turn toward the camera, locking in their identity once matched.
* **Cross-Camera Hand-Off Ready:** Pairing the face match with a secondary **OSNet ReID** body embedding in Redis allows identity transfer across cameras even when a person's face is angled away on secondary feeds.
