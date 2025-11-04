from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import config
from database import (
    init_db, get_session, ParkingSpace, OccupancyHistory,
    ParkingEvent, OccupancyPrediction, Booking, Payment
)
from parking_detector import ParkingSpaceDetector
from ml_predictor import OccupancyPredictor
import cv2
import numpy as np
from PIL import Image
import io
import base64
import random
import string
import json

app = Flask(__name__)
CORS(app)

# Initialize components
detector = ParkingSpaceDetector()
predictor = OccupancyPredictor()

# Try to load trained model
try:
    predictor.load_model()
    print("ML model loaded successfully")
except FileNotFoundError:
    print("No trained model found. Train the model first using generate_sample_data.py")


@app.route('/')
def index():
    """Render main dashboard"""
    return render_template('index.html')


@app.route('/api/parking/status', methods=['GET'])
def get_parking_status():
    """Get current parking lot status"""
    session = get_session()

    try:
        # Get all parking spaces
        spaces = session.query(ParkingSpace).all()

        # Calculate statistics
        total_spaces = len(spaces)
        occupied = sum(1 for s in spaces if s.is_occupied)
        available = total_spaces - occupied
        occupancy_rate = (occupied / total_spaces * 100) if total_spaces > 0 else 0

        space_data = [{
            'space_number': s.space_number,
            'row': s.row,
            'column': s.column,
            'is_occupied': s.is_occupied,
            'vehicle_type': s.vehicle_type,
            'last_updated': s.last_updated.isoformat() if s.last_updated else None
        } for s in spaces]

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total': total_spaces,
                'occupied': occupied,
                'available': available,
                'occupancy_rate': round(occupancy_rate, 2)
            },
            'spaces': space_data
        })

    finally:
        session.close()


@app.route('/api/parking/space/<space_number>', methods=['GET'])
def get_space_details(space_number):
    """Get details for a specific parking space"""
    session = get_session()

    try:
        space = session.query(ParkingSpace).filter_by(
            space_number=space_number
        ).first()

        if not space:
            return jsonify({'success': False, 'error': 'Space not found'}), 404

        # Get recent events for this space
        events = session.query(ParkingEvent).filter_by(
            space_number=space_number
        ).order_by(ParkingEvent.timestamp.desc()).limit(10).all()

        event_data = [{
            'event_type': e.event_type,
            'timestamp': e.timestamp.isoformat(),
            'vehicle_type': e.vehicle_type,
            'confidence': e.confidence
        } for e in events]

        return jsonify({
            'success': True,
            'space': {
                'space_number': space.space_number,
                'row': space.row,
                'column': space.column,
                'is_occupied': space.is_occupied,
                'vehicle_type': space.vehicle_type,
                'last_updated': space.last_updated.isoformat() if space.last_updated else None
            },
            'recent_events': event_data
        })

    finally:
        session.close()


@app.route('/api/occupancy/history', methods=['GET'])
def get_occupancy_history():
    """Get occupancy history for a time range"""
    hours = request.args.get('hours', default=24, type=int)
    session = get_session()

    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)

        history = session.query(OccupancyHistory).filter(
            OccupancyHistory.timestamp >= cutoff_time
        ).order_by(OccupancyHistory.timestamp).all()

        data = [{
            'timestamp': h.timestamp.isoformat(),
            'occupied': h.occupied_spaces,
            'available': h.available_spaces,
            'occupancy_rate': h.occupancy_rate
        } for h in history]

        return jsonify({
            'success': True,
            'data': data
        })

    finally:
        session.close()


@app.route('/api/occupancy/predict', methods=['GET'])
def predict_occupancy():
    """Predict future occupancy"""
    hours_ahead = request.args.get('hours', default=6, type=int)

    try:
        # Get current occupancy
        session = get_session()
        spaces = session.query(ParkingSpace).all()
        current_occupied = sum(1 for s in spaces if s.is_occupied)
        current_occupancy_rate = current_occupied / len(spaces) if len(spaces) > 0 else 0
        session.close()

        # Get predictions
        predictions = predictor.predict_future_occupancy(
            hours_ahead=hours_ahead,
            current_data={
                'current_occupancy': current_occupied,
                'avg_occupancy_last_hour': current_occupancy_rate
            }
        )

        data = [{
            'timestamp': p['target_time'].isoformat(),
            'predicted_occupancy_rate': p['predicted_occupancy_rate'],
            'predicted_occupied': p['predicted_occupied_spaces'],
            'predicted_available': p['predicted_available_spaces']
        } for p in predictions]

        return jsonify({
            'success': True,
            'predictions': data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/events/recent', methods=['GET'])
def get_recent_events():
    """Get recent parking events"""
    limit = request.args.get('limit', default=50, type=int)
    session = get_session()

    try:
        events = session.query(ParkingEvent).order_by(
            ParkingEvent.timestamp.desc()
        ).limit(limit).all()

        data = [{
            'id': e.id,
            'space_number': e.space_number,
            'event_type': e.event_type,
            'timestamp': e.timestamp.isoformat(),
            'vehicle_type': e.vehicle_type,
            'confidence': e.confidence
        } for e in events]

        return jsonify({
            'success': True,
            'events': data
        })

    finally:
        session.close()


@app.route('/api/statistics/summary', methods=['GET'])
def get_statistics_summary():
    """Get summary statistics"""
    session = get_session()

    try:
        # Current status
        spaces = session.query(ParkingSpace).all()
        total = len(spaces)
        occupied = sum(1 for s in spaces if s.is_occupied)

        # Today's events
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        entries_today = session.query(ParkingEvent).filter(
            ParkingEvent.timestamp >= today,
            ParkingEvent.event_type == 'entry'
        ).count()

        exits_today = session.query(ParkingEvent).filter(
            ParkingEvent.timestamp >= today,
            ParkingEvent.event_type == 'exit'
        ).count()

        # Average occupancy today
        history_today = session.query(OccupancyHistory).filter(
            OccupancyHistory.timestamp >= today
        ).all()

        avg_occupancy_today = np.mean([h.occupancy_rate for h in history_today]) if history_today else 0

        # Peak occupancy today
        peak_occupancy_today = max([h.occupied_spaces for h in history_today]) if history_today else 0

        return jsonify({
            'success': True,
            'current': {
                'total': total,
                'occupied': occupied,
                'available': total - occupied,
                'occupancy_rate': round((occupied / total * 100) if total > 0 else 0, 2)
            },
            'today': {
                'entries': entries_today,
                'exits': exits_today,
                'avg_occupancy_rate': round(avg_occupancy_today, 2),
                'peak_occupancy': peak_occupancy_today
            }
        })

    finally:
        session.close()


@app.route('/api/parking/update', methods=['POST'])
def update_parking_status():
    """Update parking space status (for manual updates or testing)"""
    data = request.json
    space_number = data.get('space_number')
    is_occupied = data.get('is_occupied')

    if not space_number:
        return jsonify({'success': False, 'error': 'space_number required'}), 400

    session = get_session()

    try:
        space = session.query(ParkingSpace).filter_by(
            space_number=space_number
        ).first()

        if not space:
            return jsonify({'success': False, 'error': 'Space not found'}), 404

        # Update space
        old_status = space.is_occupied
        space.is_occupied = is_occupied
        space.last_updated = datetime.now()

        if 'vehicle_type' in data:
            space.vehicle_type = data['vehicle_type']

        # Log event if status changed
        if old_status != is_occupied:
            event = ParkingEvent(
                space_number=space_number,
                event_type='entry' if is_occupied else 'exit',
                vehicle_type=data.get('vehicle_type'),
                confidence=data.get('confidence', 1.0)
            )
            session.add(event)

        session.commit()

        return jsonify({
            'success': True,
            'message': 'Space updated successfully'
        })

    finally:
        session.close()


@app.route('/api/initialize', methods=['POST'])
def initialize_parking_lot():
    """Initialize parking lot with empty spaces"""
    session = get_session()

    try:
        # Clear existing spaces
        session.query(ParkingSpace).delete()

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
                    is_occupied=False
                )
                session.add(space)
                space_id += 1

        session.commit()

        return jsonify({
            'success': True,
            'message': f'Initialized {rows * cols} parking spaces'
        })

    finally:
        session.close()


# ============ BOOKING ENDPOINTS ============

def generate_reference(prefix='BK'):
    """Generate a unique booking or payment reference"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}{timestamp}{random_str}"


@app.route('/api/bookings/available', methods=['GET'])
def get_available_slots():
    """Get available parking spaces for booking"""
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')

    if not start_time_str or not end_time_str:
        return jsonify({'success': False, 'error': 'start_time and end_time required'}), 400

    try:
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid datetime format'}), 400

    session = get_session()

    try:
        # Get all parking spaces
        all_spaces = session.query(ParkingSpace).all()

        # Get bookings that overlap with requested time
        overlapping_bookings = session.query(Booking).filter(
            Booking.status.in_(['confirmed', 'active']),
            Booking.start_time < end_time,
            Booking.end_time > start_time
        ).all()

        # Get booked space numbers
        booked_space_numbers = {b.space_number for b in overlapping_bookings}

        # Filter available spaces
        available_spaces = [
            {
                'space_number': s.space_number,
                'row': s.row,
                'column': s.column,
                'hourly_rate': s.hourly_rate,
                'is_occupied': s.is_occupied,
                'image_path': s.image_path
            }
            for s in all_spaces
            if s.space_number not in booked_space_numbers and not s.is_occupied
        ]

        return jsonify({
            'success': True,
            'available_spaces': available_spaces,
            'total_available': len(available_spaces)
        })

    finally:
        session.close()


@app.route('/api/bookings/calculate', methods=['POST'])
def calculate_booking_cost():
    """Calculate booking cost"""
    data = request.json
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    space_number = data.get('space_number')

    if not all([start_time_str, end_time_str, space_number]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    try:
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid datetime format'}), 400

    session = get_session()

    try:
        space = session.query(ParkingSpace).filter_by(space_number=space_number).first()
        if not space:
            return jsonify({'success': False, 'error': 'Space not found'}), 404

        # Calculate duration in hours
        duration = (end_time - start_time).total_seconds() / 3600
        total_cost = duration * space.hourly_rate

        return jsonify({
            'success': True,
            'duration_hours': round(duration, 2),
            'hourly_rate': space.hourly_rate,
            'total_cost': round(total_cost, 2),
            'currency': config.PAYMENT_CONFIG['currency']
        })

    finally:
        session.close()


@app.route('/api/bookings/create', methods=['POST'])
def create_booking():
    """Create a new booking"""
    data = request.json

    required_fields = ['space_number', 'customer_name', 'customer_email',
                       'vehicle_number', 'start_time', 'end_time']

    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    try:
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid datetime format'}), 400

    session = get_session()

    try:
        # Check if space exists
        space = session.query(ParkingSpace).filter_by(
            space_number=data['space_number']
        ).first()

        if not space:
            return jsonify({'success': False, 'error': 'Space not found'}), 404

        # Check if space is available for the time slot
        overlapping = session.query(Booking).filter(
            Booking.space_number == data['space_number'],
            Booking.status.in_(['confirmed', 'active']),
            Booking.start_time < end_time,
            Booking.end_time > start_time
        ).first()

        if overlapping:
            return jsonify({'success': False, 'error': 'Space not available for selected time'}), 409

        # Calculate cost
        duration = (end_time - start_time).total_seconds() / 3600
        total_amount = duration * space.hourly_rate

        # Create booking
        booking = Booking(
            booking_reference=generate_reference('BK'),
            space_number=data['space_number'],
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            customer_phone=data.get('customer_phone'),
            vehicle_number=data['vehicle_number'],
            vehicle_type=data.get('vehicle_type', 'car'),
            start_time=start_time,
            end_time=end_time,
            total_amount=total_amount,
            status='pending',
            payment_status='pending',
            notes=data.get('notes')
        )

        session.add(booking)
        session.commit()

        return jsonify({
            'success': True,
            'booking': {
                'booking_reference': booking.booking_reference,
                'space_number': booking.space_number,
                'start_time': booking.start_time.isoformat(),
                'end_time': booking.end_time.isoformat(),
                'total_amount': booking.total_amount,
                'status': booking.status,
                'payment_status': booking.payment_status
            }
        })

    finally:
        session.close()


@app.route('/api/bookings/<booking_reference>', methods=['GET'])
def get_booking_details(booking_reference):
    """Get booking details"""
    session = get_session()

    try:
        booking = session.query(Booking).filter_by(
            booking_reference=booking_reference
        ).first()

        if not booking:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404

        return jsonify({
            'success': True,
            'booking': {
                'booking_reference': booking.booking_reference,
                'space_number': booking.space_number,
                'customer_name': booking.customer_name,
                'customer_email': booking.customer_email,
                'customer_phone': booking.customer_phone,
                'vehicle_number': booking.vehicle_number,
                'vehicle_type': booking.vehicle_type,
                'start_time': booking.start_time.isoformat(),
                'end_time': booking.end_time.isoformat(),
                'total_amount': booking.total_amount,
                'status': booking.status,
                'payment_status': booking.payment_status,
                'created_at': booking.created_at.isoformat()
            }
        })

    finally:
        session.close()


@app.route('/api/bookings', methods=['GET'])
def get_all_bookings():
    """Get all bookings with optional filters"""
    status = request.args.get('status')
    from_date = request.args.get('from_date')

    session = get_session()

    try:
        query = session.query(Booking)

        if status:
            query = query.filter(Booking.status == status)

        if from_date:
            try:
                from_dt = datetime.fromisoformat(from_date)
                query = query.filter(Booking.start_time >= from_dt)
            except ValueError:
                pass

        bookings = query.order_by(Booking.created_at.desc()).limit(100).all()

        data = [{
            'booking_reference': b.booking_reference,
            'space_number': b.space_number,
            'customer_name': b.customer_name,
            'customer_email': b.customer_email,
            'vehicle_number': b.vehicle_number,
            'start_time': b.start_time.isoformat(),
            'end_time': b.end_time.isoformat(),
            'total_amount': b.total_amount,
            'status': b.status,
            'payment_status': b.payment_status
        } for b in bookings]

        return jsonify({
            'success': True,
            'bookings': data,
            'total': len(data)
        })

    finally:
        session.close()


@app.route('/api/bookings/<booking_reference>/cancel', methods=['POST'])
def cancel_booking(booking_reference):
    """Cancel a booking"""
    session = get_session()

    try:
        booking = session.query(Booking).filter_by(
            booking_reference=booking_reference
        ).first()

        if not booking:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404

        if booking.status in ['completed', 'cancelled']:
            return jsonify({'success': False, 'error': 'Cannot cancel this booking'}), 400

        # Check cancellation policy
        time_until_start = (booking.start_time - datetime.now()).total_seconds() / 3600
        if time_until_start < config.BOOKING_CONFIG['cancellation_hours']:
            return jsonify({
                'success': False,
                'error': f'Cancellation must be done at least {config.BOOKING_CONFIG["cancellation_hours"]} hours before start time'
            }), 400

        booking.status = 'cancelled'
        booking.updated_at = datetime.now()

        session.commit()

        return jsonify({
            'success': True,
            'message': 'Booking cancelled successfully'
        })

    finally:
        session.close()


# ============ PAYMENT ENDPOINTS ============

@app.route('/api/payments/process', methods=['POST'])
def process_payment():
    """Process payment for a booking (Demo mode)"""
    data = request.json
    booking_reference = data.get('booking_reference')
    payment_method = data.get('payment_method', 'card')

    if not booking_reference:
        return jsonify({'success': False, 'error': 'booking_reference required'}), 400

    session = get_session()

    try:
        booking = session.query(Booking).filter_by(
            booking_reference=booking_reference
        ).first()

        if not booking:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404

        if booking.payment_status == 'paid':
            return jsonify({'success': False, 'error': 'Booking already paid'}), 400

        # Create payment record
        payment = Payment(
            payment_reference=generate_reference('PAY'),
            booking_id=booking.id,
            amount=booking.total_amount,
            currency=config.PAYMENT_CONFIG['currency'],
            payment_method=payment_method,
            payment_gateway='demo' if config.PAYMENT_CONFIG['demo_mode'] else 'stripe',
            status='processing',
            customer_email=booking.customer_email
        )

        session.add(payment)
        session.flush()

        # In demo mode, automatically complete payment
        if config.PAYMENT_CONFIG['demo_mode']:
            payment.status = 'completed'
            payment.completed_at = datetime.now()
            payment.gateway_transaction_id = f"demo_txn_{random.randint(100000, 999999)}"

            booking.payment_status = 'paid'
            booking.payment_id = payment.payment_reference
            booking.status = 'confirmed'
        else:
            # Here you would integrate with real payment gateway (Stripe, etc.)
            # For now, we'll just mark as processing
            pass

        session.commit()

        return jsonify({
            'success': True,
            'payment': {
                'payment_reference': payment.payment_reference,
                'amount': payment.amount,
                'status': payment.status,
                'booking_reference': booking_reference
            }
        })

    finally:
        session.close()


@app.route('/api/payments/<payment_reference>', methods=['GET'])
def get_payment_status(payment_reference):
    """Get payment status"""
    session = get_session()

    try:
        payment = session.query(Payment).filter_by(
            payment_reference=payment_reference
        ).first()

        if not payment:
            return jsonify({'success': False, 'error': 'Payment not found'}), 404

        return jsonify({
            'success': True,
            'payment': {
                'payment_reference': payment.payment_reference,
                'amount': payment.amount,
                'currency': payment.currency,
                'status': payment.status,
                'payment_method': payment.payment_method,
                'payment_time': payment.payment_time.isoformat(),
                'completed_at': payment.completed_at.isoformat() if payment.completed_at else None
            }
        })

    finally:
        session.close()


# ============ IMAGE ENDPOINTS ============

@app.route('/api/parking/images/<space_number>', methods=['GET'])
def get_space_image(space_number):
    """Get image for a specific parking space"""
    session = get_session()

    try:
        space = session.query(ParkingSpace).filter_by(
            space_number=space_number
        ).first()

        if not space or not space.image_path:
            return jsonify({'success': False, 'error': 'Image not found'}), 404

        # Return image path for frontend to load
        return jsonify({
            'success': True,
            'image_url': f'/static/parking_images/{space.image_path}'
        })

    finally:
        session.close()


if __name__ == '__main__':
    # Initialize database
    init_db()

    # Run app
    app.run(
        host=config.API_CONFIG['host'],
        port=config.API_CONFIG['port'],
        debug=config.API_CONFIG['debug']
    )
