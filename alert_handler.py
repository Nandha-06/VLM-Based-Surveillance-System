import os
import cv2
import json
import logging
from datetime import datetime
from config import SAVE_ALERTS, ALERTS_DIR, DETECTION_DIR

logger = logging.getLogger(__name__)


class AlertHandler:
    """Handles anomaly alerts - saving, logging, and notifications."""
    
    def __init__(self):
        if SAVE_ALERTS:
            os.makedirs(ALERTS_DIR, exist_ok=True)
            os.makedirs(DETECTION_DIR, exist_ok=True)
        self.alerts = []
    
    def handle_alert(self, frame, analysis_result: dict):
        """
        Process an anomaly alert.
        
        Args:
            frame: The frame where anomaly was detected
            analysis_result: Analysis result from AnomalyDetector
        """
        timestamp = analysis_result['timestamp']
        description = analysis_result['description']
        persons_detected = analysis_result.get('persons_detected', False)
        detected_objects = analysis_result.get('detected_objects', [])
        
        alert = {
            'timestamp': timestamp.isoformat(),
            'description': description,
            'image_path': None,
            'persons_detected': persons_detected,
            'detected_objects': detected_objects,
            'detection_result': analysis_result.get('detection_result', {})
        }
        
        # Save the frame in alerts folder
        if SAVE_ALERTS and frame is not None:
            filename = f"alert_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(ALERTS_DIR, filename)
            cv2.imwrite(filepath, frame)
            alert['image_path'] = filepath
            logger.info(f"Alert image saved: {filepath}")
            
            # If persons detected, also save in detections folder with bounding boxes
            if persons_detected:
                detection_filename = f"detection_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
                detection_filepath = os.path.join(DETECTION_DIR, detection_filename)
                
                # Draw bounding boxes on the frame before saving
                frame_with_boxes = self._draw_bounding_boxes(frame, detected_objects)
                cv2.imwrite(detection_filepath, frame_with_boxes)
                
                # Save detection metadata
                detection_data = {
                    'timestamp': timestamp.isoformat(),
                    'description': description,
                    'image_path': detection_filepath,
                    'persons_detected': persons_detected,
                    'detected_objects': detected_objects,
                    'detection_result': analysis_result.get('detection_result', {})
                }
                
                detection_meta_file = os.path.join(DETECTION_DIR, "detections.json")
                self._append_to_json(detection_meta_file, detection_data)
                logger.info(f"Detection saved: {detection_filepath}")
        
        # Save alert metadata
        if SAVE_ALERTS:
            meta_file = os.path.join(ALERTS_DIR, "alerts.json")
            self._append_to_json(meta_file, alert)
        
        self.alerts.append(alert)
        self._notify(alert)
        
        return alert
    
    def _draw_bounding_boxes(self, frame, detected_objects):
        """Draw bounding boxes on the frame."""
        if not detected_objects:
            return frame
            
        # Make a copy of the frame to draw on
        frame_with_boxes = frame.copy()
        height, width = frame_with_boxes.shape[:2]
        
        for i, obj in enumerate(detected_objects, 1):
            # Get normalized coordinates
            x_min = obj.get('x_min', 0)
            y_min = obj.get('y_min', 0)
            x_max = obj.get('x_max', 0)
            y_max = obj.get('y_max', 0)
            
            # Convert to pixel coordinates
            x1 = int(x_min * width)
            y1 = int(y_min * height)
            x2 = int(x_max * width)
            y2 = int(y_max * height)
            
            # Draw rectangle
            cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Add label
            label = f"Person {i}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            label_x = x1
            label_y = y1 - 10 if y1 > 20 else y1 + label_size[1] + 10
            
            # Draw label background
            cv2.rectangle(frame_with_boxes, 
                         (label_x, label_y - label_size[1]), 
                         (label_x + label_size[0], label_y + 5), 
                         (0, 255, 0), -1)
            
            # Draw label text
            cv2.putText(frame_with_boxes, label, (label_x, label_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return frame_with_boxes
    
    def _append_to_json(self, filepath: str, alert: dict):
        """Append alert to JSON file."""
        alerts = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    alerts = json.load(f)
            except:
                alerts = []
        
        alerts.append(alert)
        
        with open(filepath, 'w') as f:
            json.dump(alerts, f, indent=2)
    
    def _notify(self, alert: dict):
        """Send notification for the alert."""
        # Console notification
        print("\n" + "=" * 60)
        print("🚨 ANOMALY ALERT 🚨")
        print(f"Time: {alert['timestamp']}")
        print(f"Description: {alert['description']}")
        if alert['image_path']:
            print(f"Image saved: {alert['image_path']}")
        
        # Display bounding box information if persons detected
        if alert.get('persons_detected', False) and alert.get('detected_objects'):
            print(f"\n📦 BOUNDING BOXES DETECTED:")
            for i, obj in enumerate(alert['detected_objects'], 1):
                x_min = obj.get('x_min', 0)
                y_min = obj.get('y_min', 0) 
                x_max = obj.get('x_max', 0)
                y_max = obj.get('y_max', 0)
                print(f"  Person {i}: [{x_min:.3f}, {y_min:.3f}, {x_max:.3f}, {y_max:.3f}]")
        
        print("=" * 60 + "\n")
        
        # Add custom notification logic here (email, SMS, webhook, etc.)
    
    def get_recent_alerts(self, count: int = 10) -> list:
        """Get the most recent alerts."""
        return self.alerts[-count:]
