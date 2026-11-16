# Quick Comparison for Auto-Cropping Pipelines

| Model | Prompting Style | Speed | License | Best Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Grounding DINO** | Text prompts | Moderate (GPU) | Apache 2.0 | High-precision bounding boxes for specific text queries |
| **Florence-2** | Task tokens + text | Fast (GPU/CPU) | MIT | Detecting objects *and* generating descriptive captions/labels |
| **OWLv2** | Text or image query | Moderate (GPU) | Apache 2.0 | Rare or visually distinct custom categories |
| **RF-DETR** | Fixed class list | Real-time (GPU) | Apache 2.0 | High-volume extraction of common objects (persons, vehicles) |
