# Smart Parking System - Setup Guide

A YOLOv8-powered smart parking management system with real-time occupancy detection, ML predictions, and interactive dashboard.

## Features

- 🚗 **Real-time YOLO Parking Detection** - Detects 40 parking spaces with 75-81% confidence
- 📊 **ML Occupancy Predictions** - 99.96% accuracy forecasting
- 🎯 **Interactive Dashboard** - Live parking grid with booking system
- 📈 **Analytics** - Historical data tracking and visualization
- 🖼️ **Auto-Detection** - Automatically loads demo on page load
- 💾 **Image Storage** - All detections saved to `demo_results/`

---

## Prerequisites

### Required Software

1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - ⚠️ **Important**: During installation, check "Add Python to PATH"

2. **Git** (optional, for cloning)
   - Download from: https://git-scm.com/downloads/

---

## Installation Steps

### Step 1: Download the Project

**Option A: If you have Git**
```bash
git clone <repository-url>
cd smart_parking_system
```

**Option B: If you downloaded as ZIP**
1. Extract the ZIP file
2. Open Command Prompt (CMD) or PowerShell
3. Navigate to the extracted folder:
```bash
cd path\to\smart_parking_system
```

### Step 2: Create Virtual Environment

**On Windows (Command Prompt):**
```bash
python -m venv venv
```

**On Windows (PowerShell):**
```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

**On Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**On Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

✅ You should see `(venv)` at the beginning of your command line

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- SQLAlchemy (database)
- OpenCV (image processing)
- Ultralytics (YOLOv8)
- scikit-learn (ML predictions)
- NumPy, Pandas (data processing)

**Installation time:** ~3-5 minutes depending on internet speed

---

## Project Structure

```
smart_parking_system/
├── app.py                      # Main Flask application
├── best.pt                     # YOLOv8 trained model (50MB)
├── parking.db                  # SQLite database with sample data
├── requirements.txt            # Python dependencies
├── config.py                   # Configuration settings
│
├── models/                     # ML prediction models
│   ├── occupancy_predictor.pkl # Trained ML model (581KB)
│   └── scaler.pkl              # Feature scaler (1.2KB)
│
├── data/
│   └── parking_images/         # 4 demo parking lot images
│       ├── PHOTO-2025-11-04-22-58-09.jpg    (0% occupied)
│       ├── PHOTO-2025-11-04-22-58-24.jpg    (62.5% occupied)
│       ├── PHOTO-2025-11-04-22-57-43.jpg    (20% occupied)
│       └── WhatsApp Image 2025-11-04.jpeg   (71.8% occupied)
│
├── demo_results/               # Annotated detection results (auto-generated)
│
├── static/
│   ├── css/style.css          # Dashboard styling
│   └── js/app.js              # Frontend JavaScript
│
├── templates/
│   └── index.html             # Dashboard HTML
│
├── database.py                 # Database models
├── yolo_parking_detector.py   # YOLO detection class
├── ml_predictor.py             # ML prediction model
└── README.md                   # This file
```

---

## Running the Application

### Step 1: Start the Server

Make sure you're in the project directory with virtual environment activated:

```bash
python app.py
```

You should see output like:
```
✓ YOLO model loaded successfully
✓ YOLO detector initialized successfully
Database initialized successfully!
 * Running on http://127.0.0.1:5000
 * Running on http://YOUR_IP:5000
```

### Step 2: Access the Dashboard

Open your web browser and go to:
```
http://localhost:5000
```
or
```
http://127.0.0.1:5000
```

**The dashboard will automatically load a demo detection after 2 seconds!**

---

## Using the System

### Automatic Demo Mode

When you first load the page:
1. ✅ Wait 2 seconds
2. ✅ Demo detection runs automatically
3. ✅ Parking grid shows detected occupancy
4. ✅ Annotated image appears with bounding boxes
5. ✅ Statistics update (total/occupied/available)

### Manual Detection

**Option 1: Load Demo Detection**
1. Click **"Load Demo"** button
2. System picks random demo image
3. Runs detection automatically
4. Updates grid and displays results

**Option 2: Upload Your Own Image**
1. Click **"Upload Image"** button
2. Select a parking lot image
3. Click **"Run Detection"**
4. View results instantly

### What Happens After Detection

✅ **Parking Grid** - Updates automatically (no refresh needed!)
- 🟢 Green = Available parking space
- 🔴 Red = Occupied parking space
- Space numbers: P001, P002, ... P040

✅ **Statistics Cards** - Update instantly
- Total Spaces: 40
- Occupied Spaces: X
- Available Spaces: Y
- Occupancy Rate: Z%

✅ **YOLO Detection Panel** - Shows results
- Detection statistics
- Annotated image with bounding boxes
- Space labels and confidence scores

✅ **Saved Images** - All stored in `demo_results/`
- Format: `detection_YYYYMMDD_HHMMSS.jpg` (uploaded images)
- Format: `demo_IMAGENAME_YYYYMMDD_HHMMSS.jpg` (demo images)

### Booking System

1. Click **"Book Parking"** in navigation
2. Select date and time
3. Choose available parking space
4. Enter customer details
5. Complete booking

### View Statistics

- **Occupancy History (24h)** - Chart showing past occupancy
- **Occupancy Prediction (Next 6h)** - ML-powered forecasting
- **Recent Activity** - Latest parking events
- **Today's Summary** - Daily statistics

---

## Configuration

Edit `config.py` to customize:

```python
# Parking lot configuration
PARKING_LOT_CONFIG = {
    'total_spaces': 40,      # Number of parking spaces
    'rows': 5,               # Grid rows
    'columns': 8,            # Grid columns
    'detection_interval': 5  # Detection frequency (seconds)
}

# Payment configuration
PAYMENT_CONFIG = {
    'currency': 'USD',
    'hourly_rate': 5.0,      # Hourly parking rate
    'demo_mode': True,       # Set to False for real payments
}
```

---

## API Endpoints

### YOLO Detection

**Get YOLO Status**
```bash
GET http://localhost:5000/api/detection/yolo/status
```

**Upload Image for Detection**
```bash
POST http://localhost:5000/api/detection/yolo/upload
Content-Type: multipart/form-data
Body: image=[file]
```

**Load Demo Detection**
```bash
GET http://localhost:5000/api/detection/yolo/demo
```

**Update Database from Detection**
```bash
POST http://localhost:5000/api/detection/yolo/update-database
Content-Type: multipart/form-data
Body: image=[file]
```

### Parking Status

**Get Current Status**
```bash
GET http://localhost:5000/api/parking/status
```

**Get Occupancy History**
```bash
GET http://localhost:5000/api/occupancy/history?hours=24
```

**Get Predictions**
```bash
GET http://localhost:5000/api/occupancy/predict?hours=6
```

**Get Statistics**
```bash
GET http://localhost:5000/api/statistics/summary
```

---

## Troubleshooting

### Issue: "Python not recognized"
**Solution:** Reinstall Python and check "Add Python to PATH" during installation

### Issue: "pip not recognized"
**Solution:**
```bash
python -m pip install --upgrade pip
```

### Issue: "Cannot activate virtual environment on PowerShell"
**Solution:** Run PowerShell as Administrator and execute:
```bash
Set-ExecutionPolicy RemoteSigned
```

### Issue: "YOLO model not found"
**Solution:** Ensure `best.pt` file is in the project root directory (50MB file)

### Issue: "Port 5000 already in use"
**Solution:**
1. Stop the other application using port 5000, or
2. Edit `config.py` and change the port:
```python
API_CONFIG = {
    'port': 8080,  # Change to any available port
}
```

### Issue: "No module named 'cv2'"
**Solution:**
```bash
pip install opencv-python
```

### Issue: "YOLO detection not showing on grid"
**Solution:**
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify detections in console logs
4. Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

### Issue: "Demo images not found"
**Solution:** Ensure `data/parking_images/` folder contains the 4 demo images

---

## Testing the Installation

### Quick Test Commands

**1. Test Python Installation:**
```bash
python --version
```
Should show: `Python 3.8.x` or higher

**2. Test Dependencies:**
```bash
pip list
```
Should show: flask, ultralytics, opencv-python, etc.

**3. Test YOLO Model:**
```bash
python -c "from ultralytics import YOLO; model = YOLO('best.pt'); print('YOLO model loaded!')"
```

**4. Test Server:**
```bash
curl http://localhost:5000/api/detection/yolo/status
```
or open in browser: `http://localhost:5000/api/detection/yolo/status`

Should return:
```json
{
  "yolo_available": true,
  "model_loaded": true,
  "message": "YOLO ready"
}
```

---

## Performance Metrics

### YOLO Detection
- **Speed:** 250-370ms per image
- **Confidence:** 75-81%
- **Model Size:** 50MB
- **Detects:** 40 parking spaces (P001-P040)

### ML Predictions
- **Accuracy:** 99.96%
- **Train Score:** 0.9997
- **Test Score:** 0.9996
- **Model:** Gradient Boosting Regressor

### Database
- **Type:** SQLite
- **Records:** 8,621+ historical data points
- **Size:** ~5MB

---

## Demo Workflow

**Complete Demo Flow:**
1. Start server: `python app.py`
2. Open browser: `http://localhost:5000`
3. Wait 2 seconds → Auto demo loads
4. See parking grid update automatically
5. View annotated image with bounding boxes
6. Check statistics (total/occupied/available)
7. Click "Load Demo" for different image
8. Or upload custom parking image
9. Click "Run Detection"
10. Grid updates instantly without refresh!
11. Check `demo_results/` folder for saved images

---

## Support

### Common Issues

**Q: Grid doesn't update after detection**
A: Check browser console (F12) for errors. Should see logs like:
```
Updating grid with 40 detections
Updated 40 parking spaces in grid
Stats updated - Total: 40, Occupied: 25, Available: 15
```

**Q: How to add my own parking lot images?**
A:
1. Place images in `data/parking_images/`
2. Use "Upload Image" button
3. Or they'll be used in auto-demo rotation

**Q: How to retrain the ML model?**
A:
```bash
python ml_predictor.py
```

**Q: How to reset the database?**
A:
1. Stop the server
2. Delete `parking.db`
3. Restart server (auto-creates new database)

---

## System Requirements

### Minimum:
- **CPU:** Dual-core 2.0 GHz
- **RAM:** 4 GB
- **Disk:** 500 MB free space
- **OS:** Windows 10/11, macOS 10.15+, Linux

### Recommended:
- **CPU:** Quad-core 2.5 GHz+
- **RAM:** 8 GB
- **Disk:** 1 GB free space
- **GPU:** Optional (for faster YOLO inference)

---

## Technology Stack

### Backend
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **YOLOv8** (Ultralytics) - Object detection
- **scikit-learn** - ML predictions
- **OpenCV** - Image processing
- **SQLite** - Database

### Frontend
- **Vanilla JavaScript** - No frameworks
- **Chart.js** - Data visualization
- **Responsive CSS** - Mobile-friendly
- **Fetch API** - AJAX requests

### Machine Learning
- **YOLOv8n** - Object detection model
- **Gradient Boosting** - Occupancy prediction
- **Random Forest** - Alternative ML model

---

## Quick Start Summary

### For Windows Users:

```bash
# 1. Open Command Prompt or PowerShell

# 2. Navigate to project folder
cd C:\path\to\smart_parking_system

# 3. Create virtual environment
python -m venv venv

# 4. Activate virtual environment (CMD)
venv\Scripts\activate

# 4. OR Activate virtual environment (PowerShell)
venv\Scripts\Activate.ps1

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run the application
python app.py

# 7. Open browser
# Go to: http://localhost:5000
```

### For Mac/Linux Users:

```bash
# 1. Open Terminal

# 2. Navigate to project folder
cd /path/to/smart_parking_system

# 3. Create virtual environment
python3 -m venv venv

# 4. Activate virtual environment
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run the application
python app.py

# 7. Open browser
# Go to: http://localhost:5000
```

---

## Important Files

### Must Have These Files:
- ✅ `best.pt` - YOLO model (50MB) - **REQUIRED**
- ✅ `parking.db` - Database with sample data
- ✅ `models/occupancy_predictor.pkl` - ML model
- ✅ `models/scaler.pkl` - Feature scaler
- ✅ `data/parking_images/` - 4 demo images

### Auto-Generated:
- `demo_results/` - Created automatically
- `__pycache__/` - Python cache (can delete)

---

## Next Steps After Installation

1. ✅ Test the demo detection
2. ✅ Upload your own parking lot images
3. ✅ Explore the booking system
4. ✅ Check statistics and analytics
5. ✅ Review saved images in `demo_results/`
6. ✅ Customize configuration in `config.py`
7. ✅ Train your own YOLO model (optional)

---

## License

This project is for educational/demonstration purposes.

---

## Credits

- **YOLOv8** by Ultralytics
- **Flask** web framework
- **Chart.js** for visualizations
- **OpenCV** for image processing

---

**Built with ❤️ using YOLOv8 + Flask + Machine Learning**

**Dashboard:** http://localhost:5000

**Happy Parking! 🚗**
