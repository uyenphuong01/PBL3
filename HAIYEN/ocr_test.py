'''from paddleocr import PaddleOCR
import os

# Khởi tạo OCR
ocr = PaddleOCR(lang='vi', use_textline_orientation=True)

img_path = 'assets/images/vehicle4.png'

result = None  # khai báo trước để tránh NameError

if os.path.exists(img_path):
    result = ocr.predict(img_path)

print("\n" + "="*30)
print("KẾT QUẢ NHẬN DIỆN BIỂN SỐ:")
print("="*30)

with open('results.txt', 'w', encoding='utf-8') as f:
    if result and isinstance(result, list):
        res = result[0]   # dict kết quả
        
        texts = res.get("rec_texts", [])
        scores = res.get("rec_scores", [])

        if texts:
            for text, conf in zip(texts, scores):
                print(f"- {text} (Độ tin cậy: {conf:.2f})")
                f.write(text + "\n")

            print("="*30)
            print(f"Đã lưu kết quả vào: {os.path.abspath('results.txt')}")
        else:
            print("Không tìm thấy ký tự nào trong ảnh.")
    else:
        print("Kết quả OCR rỗng.")'''

from paddleocr import PaddleOCR
import cv2
import os

# --- Cấu hình OCR ---
ocr = PaddleOCR(
    lang='vi',
    use_textline_orientation=True  # thay cho use_angle_cls / use_space_char
)

# --- Đường dẫn ảnh ---
img_path = 'assets/images/vehicle6.png'

if not os.path.exists(img_path):
    print(f"Không tìm thấy ảnh: {img_path}")
    exit()

# --- Tiền xử lý ảnh ---
img = cv2.imread(img_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

preprocessed_path = 'preprocessed.png'
cv2.imwrite(preprocessed_path, thresh)

# --- OCR ---
result = ocr.predict(preprocessed_path)

# --- Hiển thị kết quả ---
print("\n" + "="*30)
print("KẾT QUẢ NHẬN DIỆN BIỂN SỐ:")
print("="*30)

with open('results.txt', 'w', encoding='utf-8') as f:
    if result and isinstance(result, list):
        res = result[0]
        texts = res.get("rec_texts", [])
        scores = res.get("rec_scores", [])

        if texts:
            min_conf = 0.5
            for text, conf in zip(texts, scores):
                if conf >= min_conf:
                    print(f"- {text} (Độ tin cậy: {conf:.2f})")
                    f.write(text + "\n")

            print("="*30)
            print(f"Đã lưu kết quả vào: {os.path.abspath('results.txt')}")
        else:
            print("Không tìm thấy ký tự nào trong ảnh.")
    else:
        print("Kết quả OCR rỗng.")
