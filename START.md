# Smart Parking System - Setup Guide

A YOLOv8-powered smart parking management system with real-time occupancy detection, ML predictions, and analytics dashboard.

## Features

- Real-time YOLO parking space detection
- ML-based occupancy predictions (99.96% accuracy)
- Live dashboard with analytics
- Historical data tracking
- 40 parking spaces (P001-P040)

## Prerequisites

- Python 3.8+
- pip package manager
- Git (for cloning)

## Quick Start

### 1. Clone & Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd smart_parking_system

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Required Files

The repository includes:
- `best.pt` - Trained YOLOv8 model (50MB)
- `parking.db` - SQLite database with sample data
- `data/parking_images/` - 4 demo parking lot images
- `models/` - Trained ML prediction models

### 3. Run the Application

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 4. Access Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

You should see the Smart Parking Dashboard with:
- Real-time parking grid (40 spaces)
- Statistics cards
- YOLO detection panel
- Occupancy charts
- Recent events

## Using YOLO Detection

### Test with Demo Images

1. Click "Upload Image" button in YOLO Detection section
2. Select one of the images from `data/parking_images/`:
   - `PHOTO-2025-11-04-22-58-09.jpg` (0% occupied)
   - `PHOTO-2025-11-04-22-58-24.jpg` (62.5% occupied)
   - `PHOTO-2025-11-04-22-57-43.jpg` (20% occupied)
   - `WhatsApp Image 2025-11-04 at 22.58.43.jpeg` (71.8% occupied)
3. Click "Run Detection"
4. View results with annotated bounding boxes

### Detection Results

- Green boxes = Empty parking spaces
- Red boxes = Occupied parking spaces
- Space numbers (P001, P002, etc.)
- Confidence scores
- Statistics: Total, Occupied, Available, Rate

## Training Your Own Model

If you want to train YOLO on your own parking lot:

### 1. Collect Images

Take photos of your parking lot from a fixed camera angle:
- Various occupancy levels (0%-100%)
- Different times of day
- Different lighting conditions
- Minimum 100-200 images recommended

### 2. Annotate Images

Use [Roboflow](https://roboflow.com/) or [LabelImg](https://github.com/tzutalin/labelImg):
- Label each parking space as a bounding box
- Class 0: `space-empty`
- Class 1: `space-occupied`
- Export in YOLOv8 format

### 3. Train Model

```bash
# Install ultralytics
pip install ultralytics

# Create training script
python train_yolo.py
```

Sample `train_yolo.py`:
```python
from ultralytics import YOLO

# Load pretrained YOLOv8 model
model = YOLO('yolov8n.pt')

# Train on your dataset
results = model.train(
    data='path/to/data.yaml',  # Your dataset config
    epochs=100,
    imgsz=640,
    batch=16,
    name='parking_model'
)

# Save the trained model
model.save('best.pt')
```

### 4. Replace Model

Replace `best.pt` with your newly trained model and restart the server.

## Training ML Predictor

The ML predictor uses historical data to forecast occupancy:

```bash
# Train with existing database
python ml_predictor.py

# This will:
# - Load historical occupancy data
# - Train Random Forest/Gradient Boosting models
# - Save models to models/ directory
# - Display accuracy metrics (should be >99%)
```

## Database Schema

The system uses SQLite with these tables:
- `parking_spaces` - 40 parking spaces (P001-P040)
- `occupancy_history` - Historical occupancy records
- `parking_events` - Entry/exit events
- `occupancy_predictions` - ML prediction cache

## Configuration

Edit `config.py` to customize:

```python
PARKING_LOT_CONFIG = {
    'total_spaces': 40,     # Number of parking spaces
    'rows': 5,              # Grid rows
    'columns': 8,           # Grid columns
    'detection_interval': 5 # Detection frequency (seconds)
}
```

## API Endpoints

### YOLO Detection

```bash
# Check YOLO status
curl http://localhost:5000/api/detection/yolo/status

# Upload image for detection
curl -X POST http://localhost:5000/api/detection/yolo/upload \
  -F "image=@parking_lot.jpg"

# Update database from image
curl -X POST http://localhost:5000/api/detection/yolo/update-database \
  -F "image=@parking_lot.jpg"
```

### Parking Status

```bash
# Get current status
curl http://localhost:5000/api/parking/status

# Get occupancy history (24h)
curl http://localhost:5000/api/occupancy/history?hours=24

# Get predictions (next 6h)
curl http://localhost:5000/api/occupancy/predict?hours=6

# Get statistics
curl http://localhost:5000/api/statistics/summary
```

## Project Structure

```
smart_parking_system/
├── app.py                      # Flask backend & REST API
├── best.pt                     # YOLOv8 trained model (50MB)
├── parking.db                  # SQLite database
├── config.py                   # Configuration
├── requirements.txt            # Python dependencies
│
├── yolo_parking_detector.py   # YOLO detection class
├── ml_predictor.py             # ML prediction model
├── database.py                 # Database models
├── parking_detector.py         # Basic CV detector
│
├── data/
│   └── parking_images/         # Demo images (4 files)
│
├── demo_results/               # Annotated detection results
│
├── models/                     # ML models
│   ├── occupancy_predictor.pkl # Trained ML model (581KB)
│   └── scaler.pkl              # Feature scaler (1.2KB)
│
├── static/
│   ├── css/style.css          # Dashboard styling
│   └── js/app.js              # Frontend JavaScript
│
├── templates/
│   └── index.html             # Dashboard HTML
│
└── START.md                    # This file
```

## Tech Stack

### Backend
- Flask - Web framework
- SQLAlchemy - Database ORM
- YOLOv8 (Ultralytics) - Object detection
- scikit-learn - ML predictions
- OpenCV - Image processing

### Frontend
- Vanilla JavaScript
- Chart.js - Data visualization
- Responsive CSS

### Database
- SQLite - Lightweight database
- 8,621+ historical records included

### Models
- YOLOv8n - Fast detection (~300ms per image)
- Gradient Boosting - Occupancy prediction (99.96% accuracy)

## Performance

### YOLO Detection
- Speed: 250-370ms per image
- Confidence: 75-81%
- Model size: 50MB
- Can detect 40 parking spaces

### ML Predictions
- Accuracy: 99.96%
- Train score: 0.9997
- Test score: 0.9996
- Features: hour, day_of_week, current_occupancy, etc.

## Troubleshooting

### YOLO Model Not Found
```bash
# Ensure best.pt is in project root
ls -lh best.pt

# Should show: 50MB file
```

### ML Predictor Not Working
```bash
# Retrain the model
python ml_predictor.py

# Check models directory
ls -lh models/
# Should show: occupancy_predictor.pkl, scaler.pkl
```

### Database Issues
```bash
# Check database exists
ls -lh parking.db

# If missing, the app will create a new empty database
# You'll need to populate it with sample data
```

### Port Already in Use
```bash
# Change port in config.py
API_CONFIG = {
    'port': 8080,  # Change from 5000
}
```

## Demo Script

Quick demo for showcasing the system:

```bash
# 1. Start the server
python app.py

# 2. Open browser to http://localhost:5000

# 3. Run demo detection
python demo_parking_images.py

# 4. Check demo_results/ for annotated images

# 5. In browser, upload an image and run detection

# 6. Watch the dashboard update in real-time
```

## Production Deployment

For production use:

### 1. Use Production Server

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 2. Set up Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Enable HTTPS

```bash
# Using Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

### 4. Connect to Live Camera

Modify `yolo_parking_detector.py` to use your camera:

```python
# For IP camera
cap = cv2.VideoCapture('rtsp://camera-ip:554/stream')

# For USB camera
cap = cv2.VideoCapture(0)

# Run continuous detection
while True:
    ret, frame = cap.read()
    detections = detector.detect_from_frame(frame)
    # Update database every 5 seconds
```

## Contributing

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues or questions:
1. Check this START.md guide
2. Review API documentation above
3. Check demo results for expected output
4. Verify model files are present

## License

This project is for educational/demonstration purposes.

---

**Quick Links:**
- Dashboard: http://localhost:5000
- API Status: http://localhost:5000/api/detection/yolo/status
- Parking Status: http://localhost:5000/api/parking/status

**Key Files:**
- Model: `best.pt` (50MB YOLOv8 trained model)
- Database: `parking.db` (with sample data)
- Demo Images: `data/parking_images/` (4 test images)
- Results: `demo_results/` (annotated outputs)

Built with YOLOv8 + Flask + ML
