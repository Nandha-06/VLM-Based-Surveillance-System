import cv2
import time
import logging
import signal
import sys
import threading
import numpy as np
from datetime import datetime
from queue import Queue

from config import FRAME_INTERVAL, LOG_FILE
from camera import Camera
from moondream_client import MoondreamClient
from anomaly_detector import AnomalyDetector
from alert_handler import AlertHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SurveillanceSystem:
    """Main surveillance system that ties all components together."""
    
    def __init__(self, camera_index: int = None, show_preview: bool = True):
        self.camera = Camera(camera_index)
        self.moondream = MoondreamClient()
        self.detector = AnomalyDetector(self.moondream)
        self.alert_handler = AlertHandler()
        self.show_preview = show_preview
        self.running = False
        self.frame_count = 0
        self.anomaly_count = 0
        
        # Async processing setup
        self.analysis_queue = Queue(maxsize=10)  # Limit queue size to prevent memory issues
        self.analysis_thread = None
        self.last_analysis_time = 0
        
        # Motion detection setup
        self.previous_frame = None
        self.motion_threshold = 25  # Threshold for motion detection
        self.min_motion_area = 500  # Minimum area of motion to trigger analysis
        self.motion_frames_skipped = 0
        
    def start(self):
        """Start the surveillance system."""
        logger.info("Starting surveillance system...")
        
        if not self.camera.start():
            logger.error("Failed to start camera")
            return
        
        self.running = True
        self._setup_signal_handlers()
        
        # Start analysis worker thread
        self.analysis_thread = threading.Thread(target=self._analysis_worker, daemon=True)
        self.analysis_thread.start()
        
        logger.info(f"Surveillance active. Analyzing every {FRAME_INTERVAL}s")
        logger.info("Press 'q' in preview window or Ctrl+C to stop")
        
        try:
            self._run_loop()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.stop()
    
    def _detect_motion(self, frame):
        """Detect motion in the current frame compared to previous frame."""
        if self.previous_frame is None:
            self.previous_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return True  # Always analyze first frame
        
        # Convert current frame to grayscale
        current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate difference between frames
        diff = cv2.absdiff(self.previous_frame, current_gray)
        
        # Apply threshold to find motion areas
        thresh = cv2.threshold(diff, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
        
        # Find contours of motion areas
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Calculate total motion area
        motion_area = sum(cv2.contourArea(contour) for contour in contours)
        
        # Update previous frame
        self.previous_frame = current_gray
        
        # Return True if significant motion detected
        return motion_area > self.min_motion_area
    
    def _run_loop(self):
        """Main surveillance loop."""
        while self.running:
            frame = self.camera.capture_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            
            current_time = time.time()
            
            # Check for motion before queuing for analysis
            has_motion = self._detect_motion(frame)
            
            # Queue frame for analysis only if motion detected and time interval passed
            if has_motion and current_time - self.last_analysis_time >= FRAME_INTERVAL:
                try:
                    # Non-blocking queue submission
                    self.analysis_queue.put_nowait((frame, current_time))
                    self.last_analysis_time = current_time
                    self.frame_count += 1
                    logger.info(f"Motion detected! Queued frame #{self.frame_count} for analysis...")
                    self.motion_frames_skipped = 0
                except:
                    # Queue is full, skip this frame
                    logger.warning("Analysis queue full, skipping frame")
            elif not has_motion:
                self.motion_frames_skipped += 1
                if self.motion_frames_skipped % 30 == 1:  # Log every 30th skipped frame
                    logger.debug(f"No motion detected (skipped {self.motion_frames_skipped} frames)")
            
            # Show preview with motion indicator
            if self.show_preview:
                display_frame = self._add_overlay(frame)
                # Add motion indicator
                motion_color = (0, 255, 0) if has_motion else (0, 0, 255)
                cv2.putText(display_frame, "MOTION" if has_motion else "NO MOTION", 
                           (10, display_frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, motion_color, 2)
                cv2.imshow('Surveillance', display_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
            
            time.sleep(0.03)  # ~30 FPS for smooth preview
    
    def _analysis_worker(self):
        """Background thread worker for frame analysis."""
        logger.info("Analysis worker thread started")
        
        while self.running:
            try:
                # Get frame from queue (blocking with timeout)
                frame, timestamp = self.analysis_queue.get(timeout=1.0)
                
                # Process the frame (this blocks the worker thread, not main thread)
                result = self.detector.analyze(frame)
                
                if result['is_anomaly']:
                    self.anomaly_count += 1
                    self.alert_handler.handle_alert(frame, result)
                else:
                    logger.info(f"Analysis complete: {result['description'][:80]}...")
                
                # Mark task as done
                self.analysis_queue.task_done()
                
            except:
                # Queue empty or timeout, continue
                continue
        
        logger.info("Analysis worker thread stopped")
    
    def _analyze_frame(self, frame):
        """Analyze a single frame for anomalies."""
        self.frame_count += 1
        logger.info(f"Analyzing frame #{self.frame_count}...")
        
        result = self.detector.analyze(frame)
        
        if result['is_anomaly']:
            self.anomaly_count += 1
            self.alert_handler.handle_alert(frame, result)
        else:
            logger.info(f"Frame #{self.frame_count}: {result['description'][:80]}...")
    
    def _add_overlay(self, frame):
        """Add status overlay to the frame."""
        overlay = frame.copy()
        
        # Status bar background
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], 60), (0, 0, 0), -1)
        
        # Status text
        status = f"Frames: {self.frame_count} | Anomalies: {self.anomaly_count}"
        cv2.putText(overlay, status, (10, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(overlay, timestamp, (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Recording indicator
        cv2.circle(overlay, (frame.shape[1] - 30, 30), 10, (0, 0, 255), -1)
        
        return overlay

    def _setup_signal_handlers(self):
        """Setup handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Shutdown signal received")
        self.running = False
    
    def stop(self):
        """Stop the surveillance system."""
        logger.info("Stopping surveillance system...")
        self.running = False
        self.camera.stop()
        cv2.destroyAllWindows()
        
        # Print summary
        print("\n" + "=" * 40)
        print("SURVEILLANCE SESSION SUMMARY")
        print("=" * 40)
        print(f"Total frames analyzed: {self.frame_count}")
        print(f"Anomalies detected: {self.anomaly_count}")
        print("=" * 40)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='VLM-based Surveillance System')
    parser.add_argument('--camera', '-c', type=int, default=0,
                        help='Camera index (default: 0)')
    parser.add_argument('--no-preview', action='store_true',
                        help='Disable video preview window')
    parser.add_argument('--interval', '-i', type=float,
                        help='Analysis interval in seconds')
    
    args = parser.parse_args()
    
    # Override config if interval specified
    if args.interval:
        import config
        config.FRAME_INTERVAL = args.interval
    
    system = SurveillanceSystem(
        camera_index=args.camera,
        show_preview=not args.no_preview
    )
    system.start()


if __name__ == "__main__":
    main()
