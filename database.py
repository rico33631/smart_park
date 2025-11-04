from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class ParkingSpace(Base):
    """Model for individual parking spaces"""
    __tablename__ = 'parking_spaces'

    id = Column(Integer, primary_key=True)
    space_number = Column(String(10), unique=True, nullable=False)
    row = Column(Integer, nullable=False)
    column = Column(Integer, nullable=False)
    is_occupied = Column(Boolean, default=False)
    vehicle_type = Column(String(50), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    coordinates = Column(String(100))  # Store as "x1,y1,x2,y2"
    image_path = Column(String(255), nullable=True)  # Path to parking spot image
    hourly_rate = Column(Float, default=5.0)  # Hourly parking rate


class OccupancyHistory(Base):
    """Model for tracking occupancy over time"""
    __tablename__ = 'occupancy_history'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_spaces = Column(Integer, nullable=False)
    occupied_spaces = Column(Integer, nullable=False)
    available_spaces = Column(Integer, nullable=False)
    occupancy_rate = Column(Float, nullable=False)


class ParkingEvent(Base):
    """Model for tracking parking events (entry/exit)"""
    __tablename__ = 'parking_events'

    id = Column(Integer, primary_key=True)
    space_number = Column(String(10), nullable=False)
    event_type = Column(String(10), nullable=False)  # 'entry' or 'exit'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    vehicle_type = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)


class OccupancyPrediction(Base):
    """Model for storing occupancy predictions"""
    __tablename__ = 'occupancy_predictions'

    id = Column(Integer, primary_key=True)
    prediction_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    target_time = Column(DateTime, nullable=False)
    predicted_occupancy = Column(Float, nullable=False)
    predicted_available = Column(Integer, nullable=False)


def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")


def get_session():
    """Get database session"""
    return SessionLocal()


class Booking(Base):
    """Model for parking space bookings/reservations"""
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True)
    booking_reference = Column(String(20), unique=True, nullable=False)
    space_number = Column(String(10), nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100), nullable=False)
    customer_phone = Column(String(20), nullable=True)
    vehicle_number = Column(String(20), nullable=False)
    vehicle_type = Column(String(50), nullable=True)

    # Booking time
    booking_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # Status: pending, confirmed, active, completed, cancelled
    status = Column(String(20), default='pending', nullable=False)

    # Payment info
    total_amount = Column(Float, nullable=False)
    payment_status = Column(String(20), default='pending')  # pending, paid, refunded
    payment_id = Column(String(100), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payment(Base):
    """Model for payment transactions"""
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    payment_reference = Column(String(50), unique=True, nullable=False)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=True)

    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    payment_method = Column(String(50))  # card, cash, wallet, etc.
    payment_gateway = Column(String(50))  # stripe, paypal, etc.
    gateway_transaction_id = Column(String(100), nullable=True)

    # Status: pending, processing, completed, failed, refunded
    status = Column(String(20), default='pending', nullable=False)

    # Customer info
    customer_email = Column(String(100), nullable=True)

    # Timestamps
    payment_time = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Additional data
    payment_metadata = Column(Text, nullable=True)  # JSON string for additional data


if __name__ == "__main__":
    init_db()
