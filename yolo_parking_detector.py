"""
YOLO-based Parking Space Detector
Integrates trained YOLO model with the smart parking system
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path
import config

# Try to import YOLO - will work once ultralytics is installed and model is trained
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Install with: pip install ultralytics")


class YOLOParkingDetector:
    """Detects parking space occupancy using YOLO model"""

    def __init__(self, model_path=None):
        """
        Initialize YOLO detector

        Args:
            model_path: Path to trained YOLO model (.pt file)
                       If None, looks for 'best.pt' in project root
        """
        self.model = None
        self.model_loaded = False

        if not YOLO_AVAILABLE:
            print("YOLO not available. Please install: pip install ultralytics")
            return

        # Try to find model
        if model_path is None:
            # Check common locations
            possible_paths = [
                Path('best.pt'),
                Path('models/best.pt'),
                Path('models/parking_model.pt'),
                Path('yolov8n.pt'),  # Pretrained COCO model
            ]

            for path in possible_paths:
                if path.exists():
                    model_path = path
                    break

        if model_path and Path(model_path).exists():
            try:
                print(f"Loading YOLO model from: {model_path}")
                self.model = YOLO(str(model_path))
                self.model_loaded = True
                print(f"✓ YOLO model loaded successfully")
            except Exception as e:
                print(f"Error loading YOLO model: {e}")
                self.model_loaded = False
        else:
            print(f"No YOLO model found. Tried: {model_path}")
            print("Please add your trained model as 'best.pt' in the project root")

    def detect_from_image(self, image_path: str, conf_threshold: float = 0.5) -> List[Dict]:
        """
        Detect parking spaces from an image file

        Args:
            image_path: Path to image file
            conf_threshold: Confidence threshold for detections

        Returns:
            List of detection dictionaries with space info
        """
        if not self.model_loaded:
            return []

        # Run inference
        results = self.model(image_path, conf=conf_threshold)

        return self._parse_results(results[0])

    def detect_from_frame(self, frame: np.ndarray, conf_threshold: float = 0.5) -> List[Dict]:
        """
        Detect parking spaces from a video frame

        Args:
            frame: OpenCV image (numpy array)
            conf_threshold: Confidence threshold for detections

        Returns:
            List of detection dictionaries with space info
        """
        if not self.model_loaded:
            return []

        # Run inference
        results = self.model(frame, conf=conf_threshold)

        return self._parse_results(results[0])

    def _parse_results(self, result) -> List[Dict]:
        """
        Parse YOLO results into standardized format for the frontend

        Expected YOLO classes:
        - class 0: 'empty' or 'available' parking space
        - class 1: 'occupied' parking space

        Returns:
            List of dictionaries matching the database ParkingSpace schema
        """
        detections = []

        # Get boxes, confidences, and classes
        boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
        confidences = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy()

        # Get class names
        class_names = result.names

        # Process each detection
        for idx, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
            x1, y1, x2, y2 = map(int, box)
            class_id = int(cls)
            class_name = class_names[class_id]

            # Determine if space is occupied based on class
            # Common class names: 'space-empty', 'space-occupied', 'empty', 'occupied', etc.
            is_occupied = 'occupied' in class_name.lower() or class_id == 1

            # Calculate row and column based on position (simplified)
            # You may need to adjust this based on your parking lot layout
            image_height, image_width = result.orig_shape
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Estimate row and column from position
            rows = config.PARKING_LOT_CONFIG['rows']
            cols = config.PARKING_LOT_CONFIG['columns']

            row = int((center_y / image_height) * rows)
            col = int((center_x / image_width) * cols)

            # Generate space number
            space_number = f'P{idx + 1:03d}'

            detection = {
                'space_number': space_number,
                'row': row,
                'column': col,
                'is_occupied': is_occupied,
                'confidence': float(conf),
                'class_name': class_name,
                'coordinates': (x1, y1, x2, y2),
                'center': (center_x, center_y)
            }

            detections.append(detection)

        return detections

    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw detection boxes on image

        Args:
            image: OpenCV image
            detections: List of detection dictionaries

        Returns:
            Image with drawn detections
        """
        output = image.copy()

        for det in detections:
            x1, y1, x2, y2 = det['coordinates']

            # Color based on occupancy: Green = available, Red = occupied
            color = (0, 0, 255) if det['is_occupied'] else (0, 255, 0)

            # Draw box
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 3)

            # Draw label
            label = f"{det['space_number']} ({det['confidence']:.2f})"
            cv2.putText(output, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Draw status
            status = "OCCUPIED" if det['is_occupied'] else "EMPTY"
            cv2.putText(output, status, (x1 + 5, y2 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Draw summary
        total = len(detections)
        occupied = sum(1 for d in detections if d['is_occupied'])
        available = total - occupied

        summary = f"Total: {total} | Occupied: {occupied} | Available: {available}"
        cv2.putText(output, summary, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        return output

    def update_database_from_detections(self, detections: List[Dict], db_session):
        """
        Update database with detection results

        Args:
            detections: List of detection dictionaries
            db_session: SQLAlchemy database session
        """
        from database import ParkingSpace
        from datetime import datetime

        for det in detections:
            # Find or create parking space
            space = db_session.query(ParkingSpace).filter_by(
                space_number=det['space_number']
            ).first()

            if space:
                # Update existing space
                space.is_occupied = det['is_occupied']
                space.last_updated = datetime.utcnow()
            else:
                # Create new space (if needed)
                space = ParkingSpace(
                    space_number=det['space_number'],
                    row=det['row'],
                    column=det['column'],
                    is_occupied=det['is_occupied'],
                    hourly_rate=5.0  # Default rate
                )
                db_session.add(space)

        db_session.commit()


def test_yolo_detector():
    """Test YOLO detector with webcam or image"""
    detector = YOLOParkingDetector()

    if not detector.model_loaded:
        print("\nNo model loaded. To use YOLO detection:")
        print("1. Train your YOLO model on PKLot dataset")
        print("2. Save the trained model as 'best.pt'")
        print("3. Place it in the project root directory")
        print("4. Run: pip install ultralytics")
        return

    # Test with webcam
    cap = cv2.VideoCapture(0)
    print("Press 'q' to quit, 's' to save screenshot")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect parking spaces
        detections = detector.detect_from_frame(frame)

        # Draw results
        output = detector.draw_detections(frame, detections)

        cv2.imshow('YOLO Parking Detection', output)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Save screenshot
            filename = f'detection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
            cv2.imwrite(filename, output)
            print(f"Saved: {filename}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test_yolo_detector()
