import base64
import io
from PIL import Image
import moondream as md
from config import MOONDREAM_API_KEY


class MoondreamClient:
    """Client for Moondream VLM API."""
    
    def __init__(self):
        if not MOONDREAM_API_KEY:
            raise ValueError("MOONDREAM_API_KEY not set in environment")
        self.model = md.vl(api_key=MOONDREAM_API_KEY)
    
    def analyze_frame(self, frame, prompt: str) -> str:
        """
        Analyze a frame using Moondream VLM.
        
        Args:
            frame: numpy array (BGR from OpenCV) or PIL Image
            prompt: Question/prompt for the VLM
            
        Returns:
            str: Model's response
        """
        # Convert numpy array to PIL Image if needed
        if hasattr(frame, 'shape'):  # numpy array
            import cv2
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb_frame)
        else:
            image = frame
        
        # Encode image
        encoded_image = self.model.encode_image(image)
        
        # Query the model
        response = self.model.query(encoded_image, prompt)
        return response["answer"]
    
    def detect_objects(self, frame) -> dict:
        """Detect objects in the frame."""
        if hasattr(frame, 'shape'):
            import cv2
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb_frame)
        else:
            image = frame
            
        encoded_image = self.model.encode_image(image)
        result = self.model.detect(encoded_image, "person")
        
        # Log the full result to see what we get
        print(f"Detection result: {result}")
        
        return result
