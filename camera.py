import cv2
import logging
from config import CAMERA_INDEX

logger = logging.getLogger(__name__)


class Camera:
    """Handles camera capture operations."""
    
    def __init__(self, camera_index: int = None):
        self.camera_index = camera_index if camera_index is not None else CAMERA_INDEX
        self.cap = None
    
    def start(self) -> bool:
        """Initialize and start the camera."""
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            logger.error(f"Failed to open camera {self.camera_index}")
            return False
        
        # Set camera properties for better quality
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        logger.info(f"Camera {self.camera_index} started successfully")
        return True
    
    def capture_frame(self):
        """Capture a single frame from the camera."""
        if self.cap is None or not self.cap.isOpened():
            logger.error("Camera not initialized")
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            logger.error("Failed to capture frame")
            return None
        
        return frame
    
    def stop(self):
        """Release the camera."""
        if self.cap is not None:
            self.cap.release()
            logger.info("Camera released")
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
