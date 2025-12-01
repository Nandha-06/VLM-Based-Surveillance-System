import os
from dotenv import load_dotenv

load_dotenv()

# Moondream API
MOONDREAM_API_KEY = os.getenv("MOONDREAM_API_KEY")

# Camera settings
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))
FRAME_INTERVAL = float(os.getenv("FRAME_INTERVAL", 2))  # seconds between analysis

# Anomaly detection
ANOMALY_PROMPT = (
    "Describe what you see in this image and Be more specific about the objects, person, color of any objects it can be cars, person shirt"
)

# Alert keywords that indicate an anomaly was found
ALERT_KEYWORDS = [
    "intruder", "fire", "smoke", "fallen", "violence", "theft", "suspicious",
    "danger", "emergency", "unusual", "abnormal", "alert", "warning", "person",
    "breaking", "weapon", "fight", "accident"
]

# Output settings
SAVE_ALERTS = True
ALERTS_DIR = "alerts"
DETECTION_DIR = "detections"
LOG_FILE = "surveillance.log"
