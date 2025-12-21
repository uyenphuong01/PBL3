import cv2
import requests
import numpy as np
import re
import os
from paddleocr import PaddleOCR

# =========================
# CONFIG
# =========================
ROBOFLOW_API_KEY = "HEvHQ2IwQILi6IvwX4H6"
ROBOFLOW_MODEL_URL = "https://detect.roboflow.com/license-plate-detection-hyfze-gfobv/1"
VIDEO_PATH = "test.mp4"

CONF_THRESHOLD = 0.8
FPS_PROCESS = 2

SAVE_DIR = "detected_frames"
os.makedirs(SAVE_DIR, exist_ok=True)

# =========================
# INIT OCR (PIPELINE NEW)
# =========================
ocr = PaddleOCR(
    lang="en",
    use_textline_orientation=True
)

# =========================
# ROBOFLOW DETECT
# =========================
def detect_license_plate(frame):
    _, img_encoded = cv2.imencode(".jpg", frame)
    try:
        resp = requests.post(
            f"{ROBOFLOW_MODEL_URL}?api_key={ROBOFLOW_API_KEY}",
            files={"file": img_encoded.tobytes()},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print("Roboflow error:", e)
    return None

# =========================
# CROP PLATE
# =========================
def crop_plate(frame, pred):
    cx, cy = pred["x"], pred["y"]
    w, h = pred["width"], pred["height"]
    pad = int(min(w, h) * 0.08)

    x0 = int(cx - w / 2 - pad)
    y0 = int(cy - h / 2 - pad)
    x1 = int(cx + w / 2 + pad)
    y1 = int(cy + h / 2 + pad)

    H, W = frame.shape[:2]
    return frame[max(0,y0):min(H,y1), max(0,x0):min(W,x1)]

# =========================
# OCR PLATE
# =========================
def ocr_plate(img):
    if img is None or img.size == 0:
        return ""

    # Resize lớn cho dễ đọc
    img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, th = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    th_bgr = cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)

    result = ocr.predict(th_bgr)

    texts = []
    for r in result:
        texts.extend(r.get("rec_texts", []))

    plate = "".join(texts)
    plate = re.sub(r"[^A-Z0-9]", "", plate.upper())

    return plate

# =========================
# MAIN
# =========================
def main():
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(" Không mở được video")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    interval = max(1, int(fps // FPS_PROCESS))

    frame_idx = 0
    results = []
    last_plate = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % interval == 0:
            ts = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            det = detect_license_plate(frame)

            if not det:
                frame_idx += 1
                continue

            preds = det.get("predictions", [])
            if not preds:
                frame_idx += 1
                continue

            best = max(preds, key=lambda x: x.get("confidence", 0))
            conf = best.get("confidence", 0)

            if conf < CONF_THRESHOLD:
                frame_idx += 1
                continue

            crop = crop_plate(frame, best)
            plate = ocr_plate(crop)

            if plate and plate != last_plate:
                last_plate = plate
                print(f"[{ts:.2f}s] → {plate}")

                results.append(plate)

                # SAVE ORIGINAL FRAME
                fname = f"{ts:.2f}s_{conf:.2f}_{plate}.jpg"
                fname = fname.replace(":", "_")
                cv2.imwrite(os.path.join(SAVE_DIR, fname), frame)

        frame_idx += 1

    cap.release()

    with open("plate.txt", "w", encoding="utf-8") as f:
        for p in results:
            f.write(p + "\n")

    print(" DONE – plate.txt & detected_frames/")

# =========================
if __name__ == "__main__":
    main()
