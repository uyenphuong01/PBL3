from paddleocr import PaddleOCR
import cv2

class PlateOCR:
    def __init__(self):
        self.ocr = PaddleOCR(lang='en', use_textline_orientation=True)

    def read_plate(self, plate_img):
        result = self.ocr.predict(plate_img)
        texts = []

        if result and "rec_texts" in result[0]:
            texts = result[0]["rec_texts"]

        return " ".join(texts)
