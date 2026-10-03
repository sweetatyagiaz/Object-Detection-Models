class Track:

    def __init__(
        self,
        track_id,
        bbox,
        score
    ):
        self.track_id = track_id
        self.bbox = bbox
        self.score = score


class ByteTrackTracker:

    def __init__(self):
        pass

    def update(
        self,
        detections
    ):
        """
        Return tracked objects
        """
        pass