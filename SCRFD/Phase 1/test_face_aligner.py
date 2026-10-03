"""
Recommended Thresholds For your surveillance project:
=======================================================================
Scenario	                            Face Size
-----------------------------------------------------------
Very Low Quality CCTV	                40 px
Indoor Camera	                        50 px
Shop Camera	                            60 px
Office Camera	                        70 px
Enrollment Dataset	                    80 px
Premium Surveillance	                100 px

My Recommendation For NavTaksh Surveillance: MIN_FACE_SIZE = 50


Even Better (Recommended for Phase 3) Store quality metadata together with the aligned face:
------------------------------------------------------------------------------------------------
result = {
    "aligned_face": aligned_face,
    "face_size": face_size,
    "quality": quality_level
}

Quality categories:
---------------------------------------------------------------
if face_size >= 100:
    quality = "EXCELLENT"
elif face_size >= 80:
    quality = "GOOD"
elif face_size >= 50:
    quality = "ACCEPTABLE"
else:
    quality = "POOR"

This quality score can later be stored in PostgreSQL and used by AdaFace enrollment, watchlist management, and dataset curation.

"""


import cv2

from insightface.app import FaceAnalysis
from face_aligner import FaceAligner


# INPUT_IMG = "../../datasets/images/obama.jpg"
INPUT_IMG = "../../datasets/images/group_photo.jpg"

detector = FaceAnalysis(
    name="buffalo_l",
    allowed_modules=["detection"]
)

detector.prepare(
    ctx_id=0,
    det_size=(640, 640)
)

image = cv2.imread(INPUT_IMG)

aligner = FaceAligner(
    image_size=112,
    min_face_size=50
)

faces = detector.get(image)

count = 1
for face in faces:

    aligned_result = aligner.align(
        image=image,
        landmarks=face.kps,
        bbox=face.bbox
    )

    if not aligned_result["valid"]:
        continue

    aligned_face = aligned_result["aligned_face"]

    face_size = aligned_result["face_size"]

    quality = aligned_result["quality"]

    print(
        face_size,
        quality
    )