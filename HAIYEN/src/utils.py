import os
import cv2
import json
from datetime import datetime


def save_evidence(frame, track_id, plate_text, image_dir, log_dir):
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    # ===== 1️⃣ LƯU ẢNH =====
    image_name = f"violation_{timestamp}.jpg"
    image_path = os.path.join(image_dir, image_name)
    cv2.imwrite(image_path, frame)

    # ===== 2️⃣ GHI LOG JSON (CHUẨN DASHBOARD) =====
    log_data = {
        "time": timestamp,
        "plate": plate_text if plate_text else "N/A",
        "type": "Stop in Yellow Box",
        "image": f"{os.path.basename(image_dir)}/{image_name}"
    }

    log_path = os.path.join(log_dir, f"violation_{timestamp}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"[SAVE] Evidence saved: {image_name}")
