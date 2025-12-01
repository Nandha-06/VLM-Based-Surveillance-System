import logging
from datetime import datetime
from config import ANOMALY_PROMPT, ALERT_KEYWORDS

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects anomalies in surveillance frames using VLM analysis."""
    
    def __init__(self, moondream_client):
        self.client = moondream_client
        self.prompt = ANOMALY_PROMPT
        self.alert_keywords = [kw.lower() for kw in ALERT_KEYWORDS]
    
    def analyze(self, frame) -> dict:
        """
        Analyze a frame for anomalies.
        
        Returns:
            dict: {
                'timestamp': datetime,
                'description': str,
                'is_anomaly': bool,
                'confidence': str
            }
        """
        timestamp = datetime.now()
        
        try:
            # Get descriptive analysis first
            description = self.client.analyze_frame(frame, self.prompt)
            keywords_found = self._check_for_anomaly(description)
            
            # Only run person detection if anomaly keywords are found
            detection_result = {}
            detected_objects = []
            person_detected = False
            
            if keywords_found:
                detection_result = self.client.detect_objects(frame)
                detected_objects = detection_result.get("objects", [])
                person_detected = len(detected_objects) > 0
                if person_detected:
                    description += f" [PERSON DETECTED: {len(detected_objects)} person(s) found]"
            
            # Final anomaly check: require both keywords AND person detection
            is_anomaly = keywords_found and person_detected
            
            result = {
                'timestamp': timestamp,
                'description': description,
                'is_anomaly': is_anomaly,
                'confidence': 'high' if is_anomaly else 'normal',
                'persons_detected': person_detected,
                'detected_objects': detected_objects,
                'detection_result': detection_result
            }
            
            if is_anomaly:
                logger.warning(f"ANOMALY DETECTED: {description}")
            else:
                logger.debug(f"Normal: {description[:100]}...")
                
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                'timestamp': timestamp,
                'description': f"Error: {str(e)}",
                'is_anomaly': False,
                'confidence': 'error',
                'persons_detected': False,
                'detected_objects': []
            }
    
    def _check_for_anomaly(self, description: str) -> bool:
        """Check if the description indicates an anomaly."""
        desc_lower = description.lower()
        
        # Map human-related words to "person" for detection
        human_words = ["man", "woman", "person", "people", "human", "individual", "male", "female", "guy", "lady", "gentleman", "boy", "girl", "child", "adult"]
        
        # Check if any human-related words are present
        human_found = any(word in desc_lower for word in human_words)
        
        # If human found, temporarily add "person" to description for keyword checking
        if human_found and "person" not in desc_lower:
            desc_lower += " person"
        
        # Check for "no anomaly" type responses
        if "no anomaly" in desc_lower or "nothing unusual" in desc_lower:
            return False
        if "appears normal" in desc_lower or "everything looks normal" in desc_lower:
            return False
            
        # Check for alert keywords
        for keyword in self.alert_keywords:
            if keyword in desc_lower:
                return True
        
        return False
