"""
Demo script to showcase YOLO detection on your parking images
"""

from yolo_parking_detector import YOLOParkingDetector
import cv2
from pathlib import Path
import os

def demo_parking_detection():
    """Run YOLO detection on all parking images"""
    
    detector = YOLOParkingDetector()
    
    if not detector.model_loaded:
        print("❌ YOLO model not loaded!")
        print("Make sure best.pt exists in the project directory")
        return
    
    print("✓ YOLO model loaded successfully")
    print("")
    
    # Find all parking images
    image_dir = Path('data/parking_images')
    
    if not image_dir.exists():
        print(f"❌ Directory not found: {image_dir}")
        return
    
    images = list(image_dir.glob('*.jpg')) + list(image_dir.glob('*.jpeg'))
    
    if not images:
        print(f"❌ No images found in {image_dir}")
        return
    
    print(f"Found {len(images)} parking lot images")
    print("=" * 60)
    print("")
    
    # Create output directory
    output_dir = Path('demo_results')
    output_dir.mkdir(exist_ok=True)
    
    # Process each image
    for idx, image_path in enumerate(images, 1):
        print(f"\n[{idx}/{len(images)}] Processing: {image_path.name}")
        print("-" * 60)
        
        # Run detection
        detections = detector.detect_from_image(str(image_path))
        
        if not detections:
            print("  No detections found")
            continue
        
        # Show summary
        total = len(detections)
        occupied = sum(1 for d in detections if d['is_occupied'])
        available = total - occupied
        
        print(f"  ✓ Detected: {total} spaces")
        print(f"  ✓ Occupied: {occupied} ({occupied/total*100:.1f}%)")
        print(f"  ✓ Available: {available} ({available/total*100:.1f}%)")
        
        # Show top 5 detections
        print(f"\n  Top detections:")
        for det in detections[:5]:
            status = "🔴 OCCUPIED" if det['is_occupied'] else "🟢 EMPTY"
            print(f"    {det['space_number']}: {status} (conf: {det['confidence']:.2f})")
        
        # Draw and save annotated image
        image = cv2.imread(str(image_path))
        annotated = detector.draw_detections(image, detections)
        
        output_path = output_dir / f"annotated_{image_path.name}"
        cv2.imwrite(str(output_path), annotated)
        print(f"\n  💾 Saved: {output_path}")
    
    print("\n" + "=" * 60)
    print(f"✓ Demo complete! Results saved in: {output_dir}/")
    print("")
    print("Next steps:")
    print("  1. View annotated images in demo_results/")
    print("  2. Upload images via API to update database")
    print("  3. Check dashboard at http://localhost:5000")

if __name__ == "__main__":
    demo_parking_detection()
