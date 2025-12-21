from ultralytics import YOLO
import cv2

class VehicleDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, frame):
        results = self.model(frame, conf=0.4, iou=0.5, verbose=False)
        detections = []

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "class_id": cls_id,
                    "confidence": conf
                })
        return detections


if __name__ == "__main__":
    detector = VehicleDetector("models/yolov8n.pt")
    img = cv2.imread("assets/images/vehicle1.jpg")
    dets = detector.detect(img)
    print(dets)
