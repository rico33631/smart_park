"""
Parking Manager - Utilities for managing parking lot operations
"""
import cv2
import numpy as np
from datetime import datetime
from database import get_session, ParkingSpace, OccupancyHistory, ParkingEvent
from parking_detector import ParkingSpaceDetector
import config


class ParkingManager:
    """Main manager for parking lot operations"""

    def __init__(self):
        self.detector = ParkingSpaceDetector()
        self.session = get_session()

    def initialize_parking_spaces(self):
        """Initialize parking spaces in database"""
        print("Initializing parking spaces...")

        # Clear existing spaces
        self.session.query(ParkingSpace).delete()

        # Create new spaces
        rows = config.PARKING_LOT_CONFIG['rows']
        cols = config.PARKING_LOT_CONFIG['columns']

        space_id = 1
        for row in range(rows):
            for col in range(cols):
                space = ParkingSpace(
                    space_number=f'P{space_id:03d}',
                    row=row,
                    column=col,
                    is_occupied=False,
                    last_updated=datetime.now()
                )
                self.session.add(space)
                space_id += 1

        self.session.commit()
        print(f"Initialized {rows * cols} parking spaces")

    def update_from_camera(self, frame: np.ndarray):
        """Update parking status from camera frame"""
        detections = self.detector.detect_all_spaces(frame)

        for detection in detections:
            space = self.session.query(ParkingSpace).filter_by(
                space_number=detection['space_number']
            ).first()

            if space:
                old_status = space.is_occupied
                new_status = detection['is_occupied']

                # Update space
                space.is_occupied = new_status
                space.last_updated = datetime.now()

                # Log event if status changed
                if old_status != new_status:
                    event = ParkingEvent(
                        space_number=detection['space_number'],
                        event_type='entry' if new_status else 'exit',
                        confidence=detection['confidence']
                    )
                    self.session.add(event)

        self.session.commit()

        # Update occupancy history
        self.record_occupancy_snapshot()

        return detections

    def record_occupancy_snapshot(self):
        """Record current occupancy state to history"""
        spaces = self.session.query(ParkingSpace).all()

        total = len(spaces)
        occupied = sum(1 for s in spaces if s.is_occupied)
        available = total - occupied
        occupancy_rate = (occupied / total) if total > 0 else 0

        history = OccupancyHistory(
            total_spaces=total,
            occupied_spaces=occupied,
            available_spaces=available,
            occupancy_rate=occupancy_rate
        )

        self.session.add(history)
        self.session.commit()

    def get_current_status(self):
        """Get current parking lot status"""
        spaces = self.session.query(ParkingSpace).all()

        total = len(spaces)
        occupied = sum(1 for s in spaces if s.is_occupied)
        available = total - occupied

        return {
            'total': total,
            'occupied': occupied,
            'available': available,
            'occupancy_rate': (occupied / total * 100) if total > 0 else 0,
            'spaces': [{
                'space_number': s.space_number,
                'is_occupied': s.is_occupied,
                'row': s.row,
                'column': s.column
            } for s in spaces]
        }

    def simulate_random_occupancy(self, occupancy_percentage: float = 0.6):
        """Simulate random parking occupancy for testing"""
        spaces = self.session.query(ParkingSpace).all()

        for space in spaces:
            old_status = space.is_occupied
            new_status = np.random.random() < occupancy_percentage

            space.is_occupied = new_status
            space.last_updated = datetime.now()

            # Log event if status changed
            if old_status != new_status:
                event = ParkingEvent(
                    space_number=space.space_number,
                    event_type='entry' if new_status else 'exit',
                    confidence=1.0
                )
                self.session.add(event)

        self.session.commit()
        self.record_occupancy_snapshot()

        print(f"Simulated occupancy at {occupancy_percentage * 100}%")

    def close(self):
        """Close database session"""
        self.session.close()


def run_camera_monitoring():
    """Run continuous camera monitoring"""
    manager = ParkingManager()
    cap = cv2.VideoCapture(0)

    print("Starting camera monitoring...")
    print("Press 'q' to quit")
    print("Press 's' to save current frame")

    frame_count = 0
    update_interval = config.PARKING_LOT_CONFIG['detection_interval'] * config.PARKING_LOT_CONFIG['camera_fps']

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                break

            # Resize frame
            frame = cv2.resize(frame, (1280, 720))

            # Update database periodically
            if frame_count % update_interval == 0:
                print(f"Updating parking status... (frame {frame_count})")
                detections = manager.update_from_camera(frame)

                # Draw detections
                annotated_frame = manager.detector.draw_parking_spaces(frame, detections)

                # Display status
                status = manager.get_current_status()
                print(f"Available: {status['available']}/{status['total']} "
                      f"({status['occupancy_rate']:.1f}% occupied)")
            else:
                annotated_frame = frame

            # Display frame
            cv2.imshow('Smart Parking - Camera Monitor', annotated_frame)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f"parking_frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, annotated_frame)
                print(f"Saved frame to {filename}")

            frame_count += 1

    finally:
        cap.release()
        cv2.destroyAllWindows()
        manager.close()
        print("Camera monitoring stopped")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        manager = ParkingManager()

        if command == "init":
            manager.initialize_parking_spaces()

        elif command == "status":
            status = manager.get_current_status()
            print(f"\nParking Lot Status:")
            print(f"Total: {status['total']}")
            print(f"Occupied: {status['occupied']}")
            print(f"Available: {status['available']}")
            print(f"Occupancy Rate: {status['occupancy_rate']:.1f}%")

        elif command == "simulate":
            occupancy = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
            manager.simulate_random_occupancy(occupancy)

        elif command == "camera":
            manager.close()
            run_camera_monitoring()

        else:
            print("Unknown command")
            print("Available commands: init, status, simulate [occupancy], camera")

        manager.close()

    else:
        print("Parking Manager Utility")
        print("\nUsage:")
        print("  python parking_manager.py init              - Initialize parking spaces")
        print("  python parking_manager.py status            - Show current status")
        print("  python parking_manager.py simulate [0.0-1.0] - Simulate random occupancy")
        print("  python parking_manager.py camera            - Start camera monitoring")
