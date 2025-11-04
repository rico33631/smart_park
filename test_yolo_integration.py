"""
Quick test script to verify YOLO integration
"""

import requests
from pathlib import Path

BASE_URL = "http://localhost:5000"

def test_yolo_status():
    """Test 1: Check YOLO status"""
    print("=" * 50)
    print("TEST 1: Checking YOLO Status")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/api/detection/yolo/status")
    data = response.json()

    print(f"Status: {response.status_code}")
    print(f"YOLO Available: {data['yolo_available']}")
    print(f"Model Loaded: {data['model_loaded']}")
    print(f"Message: {data['message']}")
    print()

    return data['model_loaded']

def test_yolo_detection():
    """Test 2: Test detection with an image"""
    print("=" * 50)
    print("TEST 2: Testing Detection (if you have an image)")
    print("=" * 50)

    # Check if there's a test image
    possible_images = [
        'test_parking.jpg',
        'parking_lot.jpg',
        'sample_parking.jpg'
    ]

    test_image = None
    for img in possible_images:
        if Path(img).exists():
            test_image = img
            break

    if test_image:
        print(f"Found test image: {test_image}")
        print("Uploading for detection...")

        with open(test_image, 'rb') as f:
            files = {'image': f}
            response = requests.post(
                f"{BASE_URL}/api/detection/yolo/upload",
                files=files
            )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Detection successful!")
            print(f"Total spaces detected: {data['summary']['total']}")
            print(f"Occupied: {data['summary']['occupied']}")
            print(f"Available: {data['summary']['available']}")

            print(f"\nFirst 5 detections:")
            for det in data['detections'][:5]:
                status = "OCCUPIED" if det['is_occupied'] else "EMPTY"
                print(f"  {det['space_number']}: {status} (confidence: {det['confidence']:.2f})")

            # Save annotated image
            if 'annotated_image' in data:
                import base64
                img_data = data['annotated_image'].split(',')[1]
                with open('detection_result.jpg', 'wb') as f:
                    f.write(base64.b64decode(img_data))
                print(f"\n✓ Annotated image saved as: detection_result.jpg")
        else:
            print(f"✗ Detection failed: {response.status_code}")
            print(response.json())
    else:
        print("No test image found. To test detection:")
        print("1. Place a parking lot image in the project directory")
        print("2. Name it 'test_parking.jpg'")
        print("3. Run this script again")
        print("\nOr use the API directly:")
        print("  curl -X POST http://localhost:5000/api/detection/yolo/upload \\")
        print("    -F 'image=@your_image.jpg'")
    print()

def test_database_update():
    """Test 3: Test database update"""
    print("=" * 50)
    print("TEST 3: Database Update Info")
    print("=" * 50)
    print("To update the database with YOLO detections:")
    print()
    print("  curl -X POST http://localhost:5000/api/detection/yolo/update-database \\")
    print("    -F 'image=@parking_lot.jpg'")
    print()
    print("This will:")
    print("  1. Run YOLO detection on the image")
    print("  2. Update all parking spaces in the database")
    print("  3. Refresh the frontend dashboard automatically")
    print()

def main():
    print("\n" + "=" * 50)
    print("YOLO INTEGRATION TEST")
    print("=" * 50 + "\n")

    try:
        # Test 1: Check status
        model_loaded = test_yolo_status()

        if not model_loaded:
            print("⚠ YOLO model not loaded. Please check:")
            print("  1. Is best.pt in the project directory?")
            print("  2. Is ultralytics installed? (pip install ultralytics)")
            print("  3. Check server logs for errors")
            return

        # Test 2: Try detection if image available
        test_yolo_detection()

        # Test 3: Show database update info
        test_database_update()

        print("=" * 50)
        print("NEXT STEPS")
        print("=" * 50)
        print()
        print("1. Access the dashboard: http://localhost:5000")
        print()
        print("2. To test with an image:")
        print("   - Take a photo of a parking lot")
        print("   - Upload via API (see examples above)")
        print("   - Or use the test script: python yolo_parking_detector.py")
        print()
        print("3. For full integration guide:")
        print("   - Read YOLO_INTEGRATION.md")
        print()

    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server!")
        print("Please make sure the Flask server is running:")
        print("  python app.py")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
