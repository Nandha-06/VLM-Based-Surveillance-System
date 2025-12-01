# VLM-Based Surveillance System

An intelligent surveillance system that uses Vision Language Models (VLM) for real-time anomaly detection, person detection, and alert management with motion-optimized processing.

## Features

### Core Functionality
- **Real-time Camera Monitoring** - Smooth 30 FPS preview with async processing
- **VLM-Powered Analysis** - Advanced scene description using Moondream API
- **Smart Motion Detection** - Only analyzes frames with significant movement
- **Person Detection** - Bounding box detection with visual overlays
- **Dual-Stage Verification** - Requires both keywords AND actual person detection
- **Asynchronous Processing** - Non-blocking analysis prevents camera freezing

### Alert System
- **Multi-Level Alerts** - Console notifications with bounding box details
- **Dual Storage** - Separate folders for alerts and detections
- **Metadata Tracking** - JSON logs with timestamps, coordinates, and detection results
- **Visual Evidence** - Images with drawn bounding boxes for detected persons

### Performance Optimizations
- **Motion-Based Filtering** - 90%+ reduction in API calls during static scenes
- **Queue Management** - Background processing with configurable queue limits
- **Smart Frame Skipping** - Prevents memory overload during high activity
- **Resource Monitoring** - Real-time status indicators

## Requirements

- Python 3.8+
- OpenCV (`pip install opencv-python`)
- Moondream (`pip install moondream`)
- PIL (`pip install Pillow`)
- python-dotenv (`pip install python-dotenv`)
- NumPy (`pip install numpy`)

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd surveillance_system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure API key**
```bash
# Edit .env file
MOONDREAM_API_KEY=your_actual_api_key_here
```

5. **Run the system**
```bash
python surveillance.py
```

## Architecture

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Camera        │    │  Surveillance   │    │   Analysis      │
│   (OpenCV)      │───▶│   System        │───▶│   Worker Thread │
│                 │    │                 │    │                 │
│ • 30 FPS        │    │ • Motion Detect │    │ • VLM Query     │
│ • Frame Capture │    │ • Queue Mgmt    │    │ • Person Detect │
│ • Preview       │    │ • Async Process │    │ • Alert Logic   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Alert Handler  │
                       │                 │
                       │ • Save Images   │
                       │ • Draw Bounding │
                       │ • JSON Metadata │
                       │ • Notifications │
                       └─────────────────┘
```

### Data Flow Architecture
```
Camera Frame → Motion Detection → Queue → Analysis Worker → Alert Handler → Storage
     │               │              │            │               │           │
     ▼               ▼              ▼            ▼               ▼           ▼
  Live Preview    Frame Skip    Async Queue  VLM API +      Visual      JSON +
  (30 FPS)     (No Motion)    (Max 10)     Person Detect   Overlays    Images
```

### Processing Pipeline
```
1. Camera Capture (30 FPS)
   ↓
2. Motion Detection
   ├── No Motion → Skip Frame
   └── Motion Detected → Continue
   ↓
3. Queue Frame (Non-blocking)
   ↓
4. Background Analysis
   ├── VLM Query (Scene Description)
   ├── Keyword Detection
   ├── Person Detection (Bounding Boxes)
   └── Dual Verification
   ↓
5. Alert Generation
   ├── Save Original Image (alerts/)
   ├── Save with Bounding Boxes (detections/)
   └── JSON Metadata
   ↓
6. Notification & Logging
```

## Project Structure

```
surveillance_system/
├── surveillance.py          # Main system controller
├── camera.py               # Camera interface
├── moondream_client.py     # VLM API client
├── anomaly_detector.py     # Analysis logic
├── alert_handler.py        # Alert management
├── config.py               # Configuration settings
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── alerts/                # Alert images and metadata
│   ├── alert_*.jpg        # Original alert images
│   └── alerts.json       # Alert metadata
├── detections/            # Detection results
│   ├── detection_*.jpg   # Images with bounding boxes
│   └── detections.json   # Detection metadata
└── surveillance.log       # System logs
```

## Configuration

### Camera Settings (.env)
```bash
CAMERA_INDEX=0              # Camera device index
FRAME_INTERVAL=2           # Seconds between analysis
MOONDREAM_API_KEY=your_api_key_here
```

### Detection Settings (config.py)
```python
# Motion Detection
MOTION_THRESHOLD = 25       # Sensitivity (0-100)
MIN_MOTION_AREA = 500       # Minimum pixels for motion

# Alert Keywords
ALERT_KEYWORDS = [
    "intruder", "fire", "smoke", "fallen", "violence", 
    "theft", "suspicious", "danger", "emergency", 
    "unusual", "abnormal", "alert", "warning", "person",
    "breaking", "weapon", "fight", "accident"
]

# Storage
ALERTS_DIR = "alerts"
DETECTION_DIR = "detections"
```

## Workflow Diagram

### Motion-Optimized Workflow
```
┌─────────────┐
│ Start System │
└──────┬──────┘
       ▼
┌─────────────┐
│ Camera Feed │
│ (30 FPS)    │
└──────┬──────┘
       ▼
┌─────────────┐
│ Motion      │
│ Detection   │
└──────┬──────┘
       ▼
    ┌────────────┐
    │ Motion?    │
    └─────┬──────┘
   Yes │   No
        ▼   ▼
┌─────────────┐ ┌─────────────┐
│ Queue Frame │ │ Skip Frame  │
│ for Analysis│ │ (Log Stats) │
└──────┬──────┘ └─────────────┘
       ▼
┌─────────────┐
│ Background  │
│ Analysis    │
│ Worker      │
└──────┬──────┘
       ▼
┌─────────────┐
│ VLM Query   │
│ (Describe)  │
└──────┬──────┘
       ▼
┌─────────────┐
│ Keyword     │
│ Detection   │
└──────┬──────┘
       ▼
┌─────────────┐
│ Person      │
│ Detection   │
│ (Bounding   │
│ Boxes)      │
└──────┬──────┘
       ▼
┌─────────────┐
│ Dual Verify │
│ (Keywords + │
│ Person)     │
└──────┬──────┘
       ▼
┌─────────────┐
│ Generate    │
│ Alert       │
└──────┬──────┘
       ▼
┌─────────────┐
│ Save Images │
│ + Metadata  │
└──────┬──────┘
       ▼
┌─────────────┐
│ Notify User │
└──────┬──────┘
       ▼
┌─────────────┐
│ Log Results │
└─────────────┘
```

### Dual-Stage Verification Process
```
┌─────────────┐
│ Frame Input │
└──────┬──────┘
       ▼
┌─────────────┐
│ VLM Query   │
│ "Describe   │
│ what you    │
│ see"        │
└──────┬──────┘
       ▼
┌─────────────┐
│ Text        │
│ Response    │
│ "man with   │
│ dark hair"  │
└──────┬──────┘
       ▼
┌─────────────┐
│ Keyword     │
│ Mapping     │
│ "man" →     │
│ "person"    │
└──────┬──────┘
       ▼
┌─────────────┐
│ Alert       │
│ Keywords    │
│ Found?      │
└─────┬──────┘
   Yes │   No
        ▼   ▼
┌─────────────┐ ┌─────────────┐
│ Run Person  │ │ No Alert    │
│ Detection   │ │ (Normal)    │
└──────┬──────┘ └─────────────┘
       ▼
┌─────────────┐
│ Detect API  │
│ "person"    │
└──────┬──────┘
       ▼
┌─────────────┐
│ Bounding    │
│ Boxes?      │
└─────┬──────┘
   Yes │   No
        ▼   ▼
┌─────────────┐ ┌─────────────┐
│ ✅ ALERT    │ │ ❌ No Alert │
│ (Verified)  │ │ (False +ve) │
└─────────────┘ └─────────────┘
```

## Performance Metrics

### Motion Detection Impact
- **Static Scenes**: 90%+ reduction in API calls
- **Active Scenes**: Intelligent frame selection
- **Queue Management**: Prevents memory overload
- **Processing**: Smooth 30 FPS preview maintained

### Detection Accuracy
- **False Positive Reduction**: Dual-stage verification
- **Bounding Box Precision**: Pixel-level coordinates
- **Human Word Mapping**: 15+ person-related terms
- **Confidence Filtering**: Optional threshold settings

## Alert System

### Alert Structure
```json
{
  "timestamp": "2025-12-01T23:05:47.811568",
  "description": "Close-up view of a person with dark hair...",
  "image_path": "alerts/alert_20251201_230547.jpg",
  "persons_detected": true,
  "detected_objects": [
    {
      "x_min": 0.374,
      "y_min": 0.455,
      "x_max": 0.656,
      "y_max": 0.998
    }
  ],
  "detection_result": {
    "objects": [...]
  }
}
```

### Console Alert Format
```
🚨 ANOMALY ALERT 🚨
Time: 2025-12-01T23:05:47.811568
Description: Close-up view of a person with dark hair...
Image saved: alerts/alert_20251201_230547.jpg

📦 BOUNDING BOXES DETECTED:
  Person 1: [0.374, 0.455, 0.656, 0.998]
============================================================
```

## Usage Examples

### Basic Surveillance
```bash
python surveillance.py
```

### With Custom Camera
```bash
python surveillance.py --camera 1
```

### Without Preview (Headless)
```bash
python surveillance.py --no-preview
```

### Custom Analysis Interval
```bash
python surveillance.py --interval 5
```

## Troubleshooting

### Common Issues

## Output

- Alerts are saved to `alerts/` directory
- Each alert includes:
  - Timestamp
  - Description from VLM
  - Captured image
- Logs written to `surveillance.log`

## Controls

- Press `q` in preview window to quit
- Press `Ctrl+C` in terminal to stop
