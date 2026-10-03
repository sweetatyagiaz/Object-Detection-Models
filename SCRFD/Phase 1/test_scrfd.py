import cv2
from insightface.app import FaceAnalysis

app = FaceAnalysis(
    name="buffalo_l",
    allowed_modules=["detection"]
)

app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)

# image = cv2.imread("../../datasets/images/group_photo.jpg")
image = cv2.imread("../../datasets/images/obama.jpg")

faces = app.get(image)

print("Faces:", len(faces))

for face in faces:

    x1, y1, x2, y2 = map(
        int,
        face.bbox
    )

    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )

# Display Landmarks
for point in face.kps:

    x, y = map(int, point)

    cv2.circle(
        image,
        (x, y),
        3,
        (0, 0, 255),
        -1
    )

cv2.imshow(
    "SCRFD",
    image
)

cv2.waitKey(0)