from inference import get_model
import cv2
import os
from datetime import datetime

# ==============================
# 1. CẤU HÌNH
# ==============================
API_KEY = "HEvHQ2IwQILi6IvwX4H6"

MODEL_ID = "license-plate-detection-hyfze-gfobv/1"

IMAGE_PATH = "test1.jpg"
CONFIDENCE = 0.25

TARGET_CLASS = "License Plate Detection"   # 🎯 CHỈ NHẬN DIỆN BIỂN SỐ

COLOR_YELLOW = (0, 255, 255)      # màu bounding box

# ==============================
# 2. LOAD MODEL
# ==============================
print(f"Loading model: {MODEL_ID}")
model = get_model(MODEL_ID, api_key=API_KEY)

# ==============================
# 3. ĐỌC ẢNH
# ==============================
image = cv2.imread(IMAGE_PATH)
if image is None:
    raise ValueError("❌ Không đọc được ảnh test1.jpg")

# ==============================
# 4. CHẠY NHẬN DIỆN
# ==============================
results = model.infer(image, confidence=CONFIDENCE)[0]

plate_count = 0

for pred in results.predictions:

    # ❌ BỎ QUA nếu không phải License Plate
    if pred.class_name.lower() != TARGET_CLASS.lower():
        continue

    plate_count += 1

    x1 = int(pred.x - pred.width / 2)
    y1 = int(pred.y - pred.height / 2)
    x2 = int(pred.x + pred.width / 2)
    y2 = int(pred.y + pred.height / 2)

    label = f"License Plate {pred.confidence*100:.1f}%"

    cv2.rectangle(image, (x1, y1), (x2, y2), COLOR_YELLOW, 2)
    cv2.putText(
        image,
        label,
        (x1, max(y1 - 10, 25)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        COLOR_YELLOW,
        2
    )

print(f"✅ Phát hiện {plate_count} biển số")

# ==============================
# 5. LƯU ẢNH
# ==============================
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = os.path.join(output_dir, f"license_plate_{timestamp}.jpg")

cv2.imwrite(output_path, image)
print(f"📁 Ảnh đã lưu tại: {output_path}")

# ==============================
# 6. HIỂN THỊ
# ==============================
cv2.imshow("License Plate Detection", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
