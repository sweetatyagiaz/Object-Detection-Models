from insightface.app import FaceAnalysis


class SCRFDDetector:

    def __init__(self):

        self.detector = FaceAnalysis(
            name="buffalo_l",
            allowed_modules=["detection"]
        )

        self.detector.prepare(
            ctx_id=0,
            det_size=(640, 640)
        )

    def detect(self, image):

        return self.detector.get(image)