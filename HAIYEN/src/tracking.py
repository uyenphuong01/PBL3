from ultralytics import YOLO

class Tracker:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def track(self, frame):
        results = self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=0.4,
            verbose=False
        )

        tracks = []
        for r in results:
            if r.boxes.id is None:
                continue

            for box, tid in zip(r.boxes.xyxy, r.boxes.id):
                x1, y1, x2, y2 = map(int, box)
                tracks.append({
                    "track_id": int(tid),
                    "bbox": (x1, y1, x2, y2)
                })
        return tracks
