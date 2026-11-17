# Multi-Camera Surveillance Architecture (25–100 Cameras)

## 1. High-Throughput Pipeline Architecture

* **Hardware Video Decoding (NVDEC):** Never decode 50+ RTSP streams on the CPU. Use **GStreamer** with **NVIDIA DeepStream** or **FFmpeg (`h264_cuvid` / `hevc_cuvid`)** to decode H.264/H.265 camera feeds directly on the GPU's dedicated NVDEC chips.
* **Sub-Stream Ingestion:** Pull the camera's **sub-stream** (e.g., 720p at 10–15 FPS) for continuous detection and tracking. Only pull the 4K/2MP main stream snapshot when a face needs to be cropped for recognition.
* **Dynamic Batching (`nvstreammux` / Triton):** Group frames from 16 to 32 cameras into a single GPU tensor batch. Running one batched inference call on TensorRT is vastly faster than 100 sequential single-frame calls.
* **Event-Driven Recognition:** Run lightweight tracking across all 100 streams, but push cropped face/person images to an asynchronous worker queue (via **Redis** or **RabbitMQ**) for **ArcFace / AdaFace** recognition only when a person enters a doorway, gate, or perimeter zone.

---

## 2. Detection & Recognition Stack (Non-YOLO & High-Accuracy Options)

Because scaling to 100 cameras requires strict licensing clarity and top-tier accuracy for small or occluded objects, consider **Apache 2.0–licensed transformer detectors** alongside dedicated face models:

| Pipeline Stage | Recommended Models | Why It Fits 25–100 Cameras |
| :--- | :--- | :--- |
| **Person & Object Detection** | **RF-DETR** or **RT-DETRv2** (Exported to **TensorRT FP16/INT8**) | Delivers higher accuracy than standard CNN detectors, eliminates NMS post-processing bottlenecks, and uses a permissive **Apache 2.0 license**. |
| **Multi-Object Tracking** | **NVIDIA NvDCF** (in DeepStream) or **ByteTrack** | Maintains persistent IDs across frames with minimal CPU overhead so you only recognize each tracked person once per zone entry. |
| **Face Detection & Alignment** | **SCRFD** (`scrfd_10g` / `scrfd_34g` ONNX) or **YuNet** | Purpose-built for fast, accurate facial landmark extraction on entry/gate feeds before recognition. |
| **Person Recognition** | **ArcFace (`w600k_r50`)** or **AdaFace (`ir50`)** + **FAISS** | Extracts 512-d face embeddings and matches them against your family, staff, and visitor database in under 1 millisecond using **FAISS**. |

---

## 3. Hardware Sizing Guide

| Camera Count | Target FPS (Analytics) | Recommended GPU & VRAM | System RAM & CPU |
| :--- | :--- | :--- | :--- |
| **25–40 Cameras** | 10–15 FPS / stream | **1x NVIDIA RTX 4080 / 4090** (16–24 GB VRAM) or **L4** (24 GB) | 16-core CPU, 64 GB RAM |
| **50–100 Cameras** | 10–15 FPS / stream | **1x NVIDIA RTX 5090 / A4000 Ada / L40S** (32–48 GB VRAM) or **2x RTX 4090** | 32-core CPU, 128 GB RAM |

---

## 4. Backend & Dashboard Integration

* **Message Broker & State:** Use **Redis** to track active alerts and cooldown timers across all 100 streams so an intruder at the gate triggers one notification rather than hundreds.
* **Web Dashboard (Django):** Have the inference workers emit JSON events (camera ID, person name, confidence, cropped snapshot path, timestamp) via **WebSockets / Django Channels** or a REST webhook so your management dashboard updates in real time without blocking video processing.
