import cv2
import os
from datetime import datetime

from .detect_vehicle import VehicleDetector
from .detect_box import BoxDetector
from .detect_plate import PlateDetector
from .ocr import PlateOCR
from .tracking import Tracker
from .logic import ViolationLogic
from .utils import save_evidence


class ViolationSystem:
    def __init__(self):
        self.vehicle_detector = VehicleDetector("models/yolov8n.pt")
        self.box_detector = BoxDetector("models/box.pt")
        self.plate_detector = PlateDetector("models/plate.pt")

        self.tracker = Tracker("models/yolov8n.pt")
        self.ocr = None

        self.logic = ViolationLogic()

    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("[ERROR] Cannot open video")
            return

        fps = int(cap.get(cv2.CAP_PROP_FPS))
        self.logic.fps = fps
        self.logic.stop_frames = fps * 5  # >5 giây mới vi phạm

        # Folder theo từng lần chạy
        image_dir = os.path.join("evidence", "images", "images1")
        log_dir   = os.path.join("evidence", "logs", "log1")

        os.makedirs(image_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)

        os.makedirs("evidence/video", exist_ok=True)
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        output_video = f"evidence/video/{timestamp}_output.mp4"

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(
            output_video,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (w, h)
        )

        print("[INFO] Processing video...")
        print(f"[INFO] Evidence images: {image_dir}")
        print(f"[INFO] Evidence logs  : {log_dir}")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            yellow_boxes = self.box_detector.detect(frame)
            tracks = self.tracker.track(frame)

            # Draw yellow boxes
            for bx1, by1, bx2, by2 in yellow_boxes:
                cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 255, 255), 3)

            for t in tracks:
                tid = t["track_id"]
                x1, y1, x2, y2 = t["bbox"]

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame, f"ID {tid}",
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 255, 0), 2
                )

                violated = self.logic.check_violation(
                    tid,
                    (x1, y1, x2, y2),
                    yellow_boxes
                )

                if violated:
                    cv2.putText(
                        frame, "VIOLATION",
                        (x1, y2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 0, 255), 2
                    )

                    # === 1️⃣ CROP ẢNH XE ===
                    vehicle_crop = frame[y1:y2, x1:x2]
                    if vehicle_crop.size == 0:
                        continue

                    # Load OCR khi cần
                    if self.ocr is None:
                        self.ocr = PlateOCR()

                    plate_text = None

                    # === 2️⃣ DETECT BIỂN SỐ TRONG ẢNH XE ===
                    plates = self.plate_detector.detect(vehicle_crop)

                    if plates:
                        px1, py1, px2, py2 = plates[0]
                        plate_crop = vehicle_crop[py1:py2, px1:px2]

                        if plate_crop.size > 0:
                            # === 3️⃣ OCR BIỂN SỐ ===
                            plate_text = self.ocr.read_plate(plate_crop)

                            # Vẽ bbox biển số lên frame gốc
                            cv2.rectangle(
                                frame,
                                (x1 + px1, y1 + py1),
                                (x1 + px2, y1 + py2),
                                (255, 0, 0),
                                2
                            )

                            if plate_text:
                                cv2.putText(
                                    frame,
                                    plate_text,
                                    (x1 + px1, y1 + py1 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.6,
                                    (255, 0, 0),
                                    2
                                )

                    # === 4️⃣ LƯU EVIDENCE ===
                    save_evidence(
                        frame=frame,
                        track_id=tid,
                        plate_text=plate_text,
                        image_dir=image_dir,
                        log_dir=log_dir
                    )

            writer.write(frame)
            cv2.imshow("Violation Detection", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

        cap.release()
        writer.release()
        cv2.destroyAllWindows()

        print("[DONE] Finished processing")
