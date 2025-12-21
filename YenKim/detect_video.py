from inference import get_model
import cv2
import numpy as np

API_KEY = "PASTE_PRIVATE_API_KEY_HERE"
model = get_model("box_junction-kfqy9/5", api_key="HEvHQ2IwQILi6IvwX4H6")

cap = cv2.VideoCapture("test.mp4")

yellow_polygon = np.array([
    [700, 350],
    [1200, 350],
    [1550, 720],
    [650, 720]
], np.int32)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model.infer(frame)[0]

    overlay = frame.copy()
    cv2.fillPoly(overlay, [yellow_polygon], (0,255,255))
    frame = cv2.addWeighted(overlay, 0.4, frame, 0.6, 0)
    cv2.polylines(frame, [yellow_polygon], True, (0,255,255), 3)
    cv2.putText(frame, "YELLOW BOX JUNCTION",
                (750, 330),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 3)

    violation = False

    for pred in results.predictions:
        x1 = int(pred.x - pred.width / 2)
        y1 = int(pred.y - pred.height / 2)
        x2 = int(pred.x + pred.width / 2)
        y2 = int(pred.y + pred.height / 2)

        cx = int((x1 + x2) / 2)
        cy = int(y2)

        inside = cv2.pointPolygonTest(yellow_polygon, (cx, cy), False)

        color = (0,255,0)
        if inside >= 0:
            color = (0,0,255)
            violation = True

        cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
        cv2.circle(frame, (cx,cy), 5, color, -1)

    if violation:
        cv2.putText(frame, "Yellow Box: DETECTED",
                    (50, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3)

    cv2.imshow("Yellow Box Detection", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
