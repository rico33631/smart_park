import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/parking.db')

# Parking lot configuration
PARKING_LOT_CONFIG = {
    'total_spaces': 50,
    'rows': 5,
    'columns': 10,
    'camera_fps': 30,
    'detection_interval': 5  # seconds
}

# Model configuration
MODEL_CONFIG = {
    'model_path': BASE_DIR / 'models' / 'occupancy_predictor.pkl',
    'scaler_path': BASE_DIR / 'models' / 'scaler.pkl',
    'input_features': ['hour', 'day_of_week', 'is_weekend', 'current_occupancy',
                       'avg_occupancy_last_hour', 'avg_occupancy_same_hour_last_week'],
    'prediction_horizon': 6  # hours
}

# API configuration
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}

# Image processing configuration
IMAGE_CONFIG = {
    'image_width': 1920,
    'image_height': 1080,
    'parking_space_width': 100,
    'parking_space_height': 200,
    'confidence_threshold': 0.7
}

# Paths
MODELS_DIR = BASE_DIR / 'models'
DATA_DIR = BASE_DIR / 'data'
STATIC_DIR = BASE_DIR / 'static'
TEMPLATES_DIR = BASE_DIR / 'templates'
IMAGES_DIR = DATA_DIR / 'parking_images'

# Payment configuration
PAYMENT_CONFIG = {
    'currency': 'USD',
    'hourly_rate': 5.0,
    'demo_mode': True,  # Set to False for real payment gateway
    'stripe_public_key': os.getenv('STRIPE_PUBLIC_KEY', 'pk_test_demo'),
    'stripe_secret_key': os.getenv('STRIPE_SECRET_KEY', 'sk_test_demo'),
}

# Booking configuration
BOOKING_CONFIG = {
    'min_booking_hours': 1,
    'max_booking_hours': 24,
    'advance_booking_days': 7,  # How many days in advance can book
    'cancellation_hours': 2,  # Hours before start time to allow cancellation
}

# Create directories if they don't exist
for directory in [MODELS_DIR, DATA_DIR, STATIC_DIR, TEMPLATES_DIR, IMAGES_DIR]:
    directory.mkdir(exist_ok=True)
