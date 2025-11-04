import cv2
import numpy as np
from typing import List, Tuple, Dict
from datetime import datetime
import config


class ParkingSpaceDetector:
    """Detects parking space occupancy using computer vision"""

    def __init__(self):
        self.parking_spaces = []
        self.previous_frame = None

    def define_parking_spaces(self, image_shape: Tuple[int, int]) -> List[Dict]:
        """
        Define parking space regions based on image dimensions
        Returns list of parking space coordinates
        """
        spaces = []
        rows = config.PARKING_LOT_CONFIG['rows']
        cols = config.PARKING_LOT_CONFIG['columns']

        height, width = image_shape[:2]
        space_width = width // cols
        space_height = height // rows

        space_id = 1
        for row in range(rows):
            for col in range(cols):
                x1 = col * space_width
                y1 = row * space_height
                x2 = x1 + space_width
                y2 = y1 + space_height

                spaces.append({
                    'id': space_id,
                    'space_number': f'P{space_id:03d}',
                    'row': row,
                    'column': col,
                    'coordinates': (x1, y1, x2, y2)
                })
                space_id += 1

        self.parking_spaces = spaces
        return spaces

    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for better detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 25, 16
        )

        # Apply median blur to further reduce noise
        median = cv2.medianBlur(thresh, 5)

        # Dilate to fill gaps
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(median, kernel, iterations=1)

        return dilated

    def detect_occupancy_by_pixels(self, frame: np.ndarray, space: Dict) -> Tuple[bool, float]:
        """
        Detect if parking space is occupied based on pixel intensity
        Returns (is_occupied, confidence)
        """
        x1, y1, x2, y2 = space['coordinates']

        # Extract region of interest
        roi = frame[y1:y2, x1:x2]

        if roi.size == 0:
            return False, 0.0

        # Calculate the number of white pixels (indicating presence of vehicle)
        white_pixels = cv2.countNonZero(roi)
        total_pixels = roi.shape[0] * roi.shape[1]

        # Calculate occupancy percentage
        occupancy_percentage = white_pixels / total_pixels

        # Threshold for determining occupancy (adjust based on testing)
        threshold = 0.25
        is_occupied = occupancy_percentage > threshold

        # Confidence based on how far from threshold
        confidence = min(abs(occupancy_percentage - threshold) / threshold, 1.0)

        return is_occupied, confidence

    def detect_motion(self, current_frame: np.ndarray, space: Dict) -> bool:
        """Detect motion in parking space using frame differencing"""
        if self.previous_frame is None:
            return False

        x1, y1, x2, y2 = space['coordinates']

        # Extract ROI from both frames
        curr_roi = current_frame[y1:y2, x1:x2]
        prev_roi = self.previous_frame[y1:y2, x1:x2]

        if curr_roi.size == 0 or prev_roi.size == 0:
            return False

        # Calculate absolute difference
        diff = cv2.absdiff(curr_roi, prev_roi)

        # Count pixels with significant change
        motion_pixels = cv2.countNonZero(diff)
        total_pixels = diff.shape[0] * diff.shape[1]

        motion_percentage = motion_pixels / total_pixels

        # Motion detected if more than 10% pixels changed
        return motion_percentage > 0.1

    def detect_all_spaces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect occupancy for all parking spaces
        Returns list of space statuses
        """
        if not self.parking_spaces:
            self.define_parking_spaces(frame.shape)

        # Preprocess frame
        processed = self.preprocess_frame(frame)

        results = []
        for space in self.parking_spaces:
            is_occupied, confidence = self.detect_occupancy_by_pixels(processed, space)
            has_motion = self.detect_motion(processed, space)

            results.append({
                'space_number': space['space_number'],
                'row': space['row'],
                'column': space['column'],
                'is_occupied': is_occupied,
                'confidence': confidence,
                'has_motion': has_motion,
                'coordinates': space['coordinates']
            })

        # Update previous frame
        self.previous_frame = processed.copy()

        return results

    def draw_parking_spaces(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw parking spaces on frame with color coding"""
        output = frame.copy()

        for detection in detections:
            x1, y1, x2, y2 = detection['coordinates']

            # Color coding: Green = available, Red = occupied, Yellow = motion detected
            if detection['has_motion']:
                color = (0, 255, 255)  # Yellow
            elif detection['is_occupied']:
                color = (0, 0, 255)  # Red
            else:
                color = (0, 255, 0)  # Green

            # Draw rectangle
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

            # Draw space number
            cv2.putText(
                output, detection['space_number'],
                (x1 + 5, y1 + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
            )

            # Draw confidence
            conf_text = f"{detection['confidence']:.2f}"
            cv2.putText(
                output, conf_text,
                (x1 + 5, y2 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
            )

        # Draw summary
        total = len(detections)
        occupied = sum(1 for d in detections if d['is_occupied'])
        available = total - occupied

        summary = f"Total: {total} | Occupied: {occupied} | Available: {available}"
        cv2.putText(
            output, summary,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2
        )

        return output


def test_detector_with_webcam():
    """Test the detector using webcam"""
    detector = ParkingSpaceDetector()
    cap = cv2.VideoCapture(0)

    print("Press 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize frame for better performance
        frame = cv2.resize(frame, (1280, 720))

        # Detect parking spaces
        detections = detector.detect_all_spaces(frame)

        # Draw results
        output = detector.draw_parking_spaces(frame, detections)

        cv2.imshow('Smart Parking System', output)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test_detector_with_webcam()
