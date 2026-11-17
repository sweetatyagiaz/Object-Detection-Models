# End-to-End Design Flow: 25–100 Camera Residential Security Surveillance

This document outlines the complete data and execution flow for a high-throughput residential security system scaling to **25–100 IP cameras**, combining **NVDEC hardware decoding**, **RF-DETR / RT-DETRv2**, **NvDCF / ByteTrack**, and **SCRFD + ArcFace/AdaFace + FAISS**.

---

## 1. System Design Flow Diagram

```text
[25-100 IP Cameras (RTSP)]
       │
       ├──► Sub-Streams (720p @ 15 FPS) ──► [NVDEC Hardware Video Decoder]
       │                                              │
       │                                    [Dynamic Frame Batcher] (16-32 frames/batch)
       │                                              │
       │                                    [RF-DETR / RT-DETRv2 (TensorRT)]
       │                                              │ (Person Bounding Boxes)
       │                                    [NvDCF / ByteTrack Tracker]
       │                                              │ (Assigns track_id)
       │                                    ┌─────────┴─────────┐
       │                                    ▼                   ▼
       │                         [Identity in Redis?]     [Not in Redis]
       │                                    │                   │
       │                                  (YES)               (NO)
       │                                    │                   ▼
       │                                    │         [Crop Person / Head]
       │                                    │                   │
       │                                    │         [SCRFD Face Alignment]
       │                                    │                   │
       │                                    │         [ArcFace / AdaFace] (512-d)
       │                                    │                   │
       │                                    │         [FAISS Vector Search]
       │                                    │                   │
       │                                    │         [Cache Result in Redis]
       │                                    └─────────┬─────────┘
       │                                              │
       └──► Main Stream Snapshot (On Alert) ──────────┼──► [Alert & Event Engine]
                                                                  │
                                            ┌─────────────────────┼─────────────────────┐
                                            ▼                     ▼                     ▼
                                   [Django WebSockets]    [PostgreSQL Logs]   [Push / SMS Alerts]
```

---

## 2. Step-by-Step Execution Flow

### Step 1: Dual-Stream Ingestion & Hardware Decode
* **Dual RTSP Streams:** Every IP camera exposes two RTSP streams: a lightweight **sub-stream** (`720p` at `10–15 FPS`) for continuous analytics and a **high-resolution main stream** (`1080p/4K`) pulled on demand for high-clarity evidence snapshots.
* **GPU Video Decoding:** **NVDEC** decodes all 25–100 H.264/H.265 streams directly inside GPU memory, preventing CPU bottlenecks.

### Step 2: Dynamic Batching & Person Detection
* **Batch Formation:** Decoded frames enter a ring buffer and are grouped into batches of **16 to 32 frames**.
* **Transformer Detection:** **RF-DETR** or **RT-DETRv2** (compiled to TensorRT FP16/INT8) executes a single batched forward pass to output person bounding boxes (`[x1, y1, x2, y2, confidence]`) without NMS post-processing overhead.

### Step 3: Persistent Tracking & State Lookup
* **ID Assignment:** **NvDCF** or **ByteTrack** associates detections across consecutive frames and assigns a persistent `track_id` per camera.
* **Redis Cache Check:** The worker queries **Redis** (`cam:{id}:track:{track_id}`) to determine whether that tracked individual has already been identified.

### Step 4: Conditional Recognition (Async Worker Path)
* **Cache Hit:** If a verified identity (e.g., `"Family - Arjun"`) exists in Redis, the pipeline bypasses face recognition models completely and attaches the cached name to the bounding box.
* **Cache Miss:** If the `track_id` is new or unresolved (`"Scanning..."`), the cropped person region is routed to **SCRFD** for facial landmark alignment, **ArcFace** or **AdaFace** for 512-dimensional embedding extraction, and **FAISS** for sub-millisecond cosine similarity matching.
* **Adaptive TTL Caching:**
  * **Verified Match:** Cached in Redis for **30 seconds** so recognition is not repeated on every frame.
  * **Unrecognized / Side Profile:** Cached with a short **2-second retry TTL** so the system automatically re-evaluates as soon as the person turns toward the camera.

### Step 5: Zone Rules, Cooldowns & Dashboard Delivery
* **Spatial & Time-Based Evaluation:** Tracked identities are checked against **PolygonZone** boundaries (such as main gates, driveways, and backyard perimeters) alongside time-of-day rules.
* **Event Dispatch:** When an `"Unknown"` person enters a restricted zone—or a registered family member arrives at an entry point—the alert engine grabs a high-res main-stream snapshot, publishes a JSON event via **Redis Pub/Sub** to **Django Channels** (WebSockets), logs the incident in **PostgreSQL**, and triggers mobile/SMS notifications with a cooldown timer to prevent alert spam.
