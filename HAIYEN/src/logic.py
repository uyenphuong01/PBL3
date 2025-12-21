import math

class ViolationLogic:
    def __init__(self, fps=30, stop_time_threshold=5, move_threshold=5):
        """
        fps: FPS video
        stop_time_threshold: số giây đứng yên để vi phạm
        move_threshold: ngưỡng pixel coi là không di chuyển
        """
        self.fps = fps
        self.stop_frames = stop_time_threshold * fps
        self.move_threshold = move_threshold

        self.last_position = {}   # track_id -> (cx, cy)
        self.stop_counter = {}    # track_id -> số frame đứng yên

    def inside_box(self, bbox, box):
        x1, y1, x2, y2 = bbox
        bx1, by1, bx2, by2 = box

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        return bx1 <= cx <= bx2 and by1 <= cy <= by2, cx, cy

    def check_violation(self, track_id, bbox, boxes):
        for box in boxes:
            inside, cx, cy = self.inside_box(bbox, box)

            if not inside:
                # Ra khỏi box → reset
                self.stop_counter[track_id] = 0
                self.last_position[track_id] = (cx, cy)
                return False

            # ===============================
            # TÍNH VẬN TỐC
            # ===============================
            if track_id not in self.last_position:
                self.last_position[track_id] = (cx, cy)
                self.stop_counter[track_id] = 0
                return False

            px, py = self.last_position[track_id]
            dist = math.hypot(cx - px, cy - py)

            self.last_position[track_id] = (cx, cy)

            # ===============================
            # ĐỨNG YÊN?
            # ===============================
            if dist < self.move_threshold:
                self.stop_counter[track_id] += 1
            else:
                self.stop_counter[track_id] = 0

            # DEBUG (rất nên giữ khi demo)
            print(f"[DEBUG] ID {track_id} | stop_frames: {self.stop_counter[track_id]}")

            # ===============================
            # VI PHẠM
            # ===============================
            if self.stop_counter[track_id] >= self.stop_frames:
                return True

        return False
