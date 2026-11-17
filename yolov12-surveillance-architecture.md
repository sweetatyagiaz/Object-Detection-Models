# YOLOv12 Security Surveillance Architecture

## Recommended Architecture by Environment

| Environment | Primary Detection Focus | Best Recognition / Secondary Pair | Key Alert Logic |
| :--- | :--- | :--- | :--- |
| **Traffic & Roads** | Cars, trucks, two-wheelers, pedestrians (`yolo12m.pt`) | **FastALPR** or **PaddleOCR** (License Plate Recognition) | Wrong-way driving, speed estimation via line-crossing, or no-parking zone violations. |
| **Campus & Grounds** | People, backpacks, vehicles, weapons (`yolo12s.pt` / `yolo12m.pt`) | **BoxMOT + OSNet** (Cross-camera Person ReID) & **ArcFace** at gates | Perimeter breaches, loitering near restricted labs, and tracking individuals across buildings. |
| **House & Residential** | People, faces, pets, packages (`yolo12n.pt` / `yolo12s.pt`) | **InsightFace (ArcFace)** (Family/Staff Whitelist) | Stranger detection at doors, night-time driveway intrusion, and package drop-off/pickup alerts. |

---

## How to Structure a Unified System

1. **Shared YOLOv12 Backbone:** Run **YOLOv12** (`yolo12s.pt` for edge devices or `yolo12m.pt` for GPU servers) as your core detector to extract bounding boxes and persistent tracker IDs (`ByteTrack` or `BoT-SORT`) across all RTSP camera streams.
2. **Conditional Secondary Models (Save Compute):** Trigger heavy recognition models only when specific conditions are met:
   * **Home / Campus Gates:** Run **InsightFace** only when a tracked person enters a door or gate polygon zone.
   * **Traffic Feeds:** Run **PaddleOCR** only when a vehicle crosses a virtual tripwire line to read the license plate once.
   * **Campus Corridors:** Use **OSNet ReID** to maintain the same visitor ID as they move from an outdoor camera to an indoor camera.
3. **Time-Based & Zone Rules:** Use `supervision.PolygonZone` and `supervision.LineZone` to apply different rules per camera—such as alerting on any person in a home driveway after 11:00 PM, while only flagging unauthorized faces at a campus gate during daytime hours.
