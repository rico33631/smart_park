# Smart Parking System - Quick Start

## Installation

```bash
cd smart_parking_system
pip install -r requirements.txt
```

## Setup Database

```bash
python generate_sample_data.py
```

## Run Application

```bash
python app.py
```

Access dashboard at: **http://localhost:5000**

## Test with Simulation

```bash
# Simulate 70% occupancy
python parking_manager.py simulate 0.7

# Check status
python parking_manager.py status
```

## API Endpoints

```bash
# Get parking status
curl http://localhost:5000/api/parking/status

# Get predictions
curl http://localhost:5000/api/occupancy/predict

# Get statistics
curl http://localhost:5000/api/statistics/summary
```

## Stop Server

```bash
pkill -f "python app.py"
```

---

## For Production (When Training is Complete)

### 1. Add Your Trained Model
Place your trained YOLO model in the project root:
```
smart_parking_system/
├── your_trained_model.pt  <-- Put trained model here
```

Or in a models folder:
```bash
mkdir -p models
# Copy your trained model
cp path/to/trained_model.pt models/parking_model.pt
```

### 2. Add PKLot Dataset
Place dataset in `data/PKLot/` folder:
```
smart_parking_system/
├── data/
│   └── PKLot/
│       ├── train/
│       │   ├── images/
│       │   └── labels/
│       ├── valid/
│       │   ├── images/
│       │   └── labels/
│       └── test/
│           ├── images/
│           └── labels/
```

### 3. Update Detection Code
In `parking_detector.py`, update to use your trained model:
```python
from ultralytics import YOLO
model = YOLO('your_trained_model.pt')  # or 'models/parking_model.pt'
```
