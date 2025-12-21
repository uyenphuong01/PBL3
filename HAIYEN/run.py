from src.detect_violation import ViolationSystem

if __name__ == "__main__":
    system = ViolationSystem()
    system.process_video("assets/video/2.mp4")
