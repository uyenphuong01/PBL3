import os
from pathlib import Path

class Config:
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    MODELS_DIR = BASE_DIR / "models"
    ASSETS_DIR = BASE_DIR / "assets"
    EVIDENCE_DIR = BASE_DIR / "evidence"
    
    # Model paths
    VEHICLE_MODEL = MODELS_DIR / "yolov8n.pt"
    PLATE_MODEL = MODELS_DIR / "plate.pt"
    BOX_MODEL = MODELS_DIR / "box.pt"
    
    # Detection thresholds
    VEHICLE_CONF = 0.5
    PLATE_CONF = 0.6
    BOX_CONF = 0.7
    
    # Tracking
    MAX_AGE = 30
    MIN_HITS = 3
    IOU_THRESHOLD = 0.3
    
    # Violation rules
    STOP_TIME_THRESHOLD = 3.0  # seconds
    JUNCTION_BLOCK_TIME = 2.0  # seconds
    
    # Evidence保存
    EVIDENCE_FORMATS = {
        'image': 'jpg',
        'video': 'mp4',
        'log': 'json'
    }
    
    # API settings
    API_HOST = "0.0.0.0"
    API_PORT = 8000