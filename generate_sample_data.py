"""
Generate sample parking data for training and testing the ML model
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from database import init_db, get_session, OccupancyHistory, ParkingEvent, ParkingSpace
import config
from ml_predictor import OccupancyPredictor


def generate_realistic_occupancy_pattern(hour, day_of_week):
    """
    Generate realistic occupancy based on time and day patterns

    Typical patterns:
    - Weekdays: Peak during work hours (9-17)
    - Weekends: More even distribution, peak in afternoon
    - Night hours: Low occupancy
    """
    is_weekend = day_of_week >= 5

    if is_weekend:
        # Weekend pattern
        if 0 <= hour < 7:  # Late night/early morning
            base_occupancy = 0.15
        elif 7 <= hour < 10:  # Morning
            base_occupancy = 0.35
        elif 10 <= hour < 14:  # Late morning/early afternoon
            base_occupancy = 0.65
        elif 14 <= hour < 20:  # Afternoon/evening
            base_occupancy = 0.75
        elif 20 <= hour < 22:  # Evening
            base_occupancy = 0.50
        else:  # Late evening
            base_occupancy = 0.25
    else:
        # Weekday pattern
        if 0 <= hour < 6:  # Late night/early morning
            base_occupancy = 0.10
        elif 6 <= hour < 8:  # Early morning arrival
            base_occupancy = 0.40
        elif 8 <= hour < 10:  # Morning rush
            base_occupancy = 0.85
        elif 10 <= hour < 12:  # Late morning
            base_occupancy = 0.90
        elif 12 <= hour < 14:  # Lunch time (some leave)
            base_occupancy = 0.75
        elif 14 <= hour < 17:  # Afternoon
            base_occupancy = 0.85
        elif 17 <= hour < 19:  # Evening rush (people leaving)
            base_occupancy = 0.60
        elif 19 <= hour < 22:  # Evening
            base_occupancy = 0.30
        else:  # Late evening
            base_occupancy = 0.15

    # Add some random variation
    noise = np.random.normal(0, 0.05)
    occupancy = np.clip(base_occupancy + noise, 0, 1)

    return occupancy


def generate_historical_data(days=60):
    """Generate historical parking data for training"""
    print(f"Generating {days} days of historical data...")

    data = []
    start_date = datetime.now() - timedelta(days=days)
    total_spaces = config.PARKING_LOT_CONFIG['total_spaces']

    # Generate data every 5 minutes
    current_date = start_date
    end_date = datetime.now()

    while current_date < end_date:
        hour = current_date.hour
        day_of_week = current_date.weekday()

        # Generate occupancy
        occupancy_rate = generate_realistic_occupancy_pattern(hour, day_of_week)
        occupied_spaces = int(occupancy_rate * total_spaces)
        available_spaces = total_spaces - occupied_spaces

        data.append({
            'timestamp': current_date,
            'total_spaces': total_spaces,
            'occupied_spaces': occupied_spaces,
            'available_spaces': available_spaces,
            'occupancy_rate': occupancy_rate
        })

        # Increment by 5 minutes
        current_date += timedelta(minutes=5)

    print(f"Generated {len(data)} data points")
    return pd.DataFrame(data)


def populate_database_with_sample_data(days=60):
    """Populate database with sample historical data"""
    print("Initializing database...")
    init_db()

    session = get_session()

    try:
        # Clear existing data
        print("Clearing existing data...")
        session.query(OccupancyHistory).delete()
        session.query(ParkingEvent).delete()
        session.query(ParkingSpace).delete()

        # Initialize parking spaces
        print("Creating parking spaces...")
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
                session.add(space)
                space_id += 1

        session.commit()
        print(f"Created {rows * cols} parking spaces")

        # Generate and insert historical data
        print("Generating historical occupancy data...")
        df = generate_historical_data(days)

        print("Inserting data into database...")
        for _, row in df.iterrows():
            history = OccupancyHistory(
                timestamp=row['timestamp'],
                total_spaces=int(row['total_spaces']),
                occupied_spaces=int(row['occupied_spaces']),
                available_spaces=int(row['available_spaces']),
                occupancy_rate=float(row['occupancy_rate'])
            )
            session.add(history)

        session.commit()
        print(f"Inserted {len(df)} occupancy history records")

        # Generate some parking events
        print("Generating parking events...")
        spaces = session.query(ParkingSpace).all()
        event_count = 0

        for i in range(0, len(df), 12):  # Every hour
            timestamp = df.iloc[i]['timestamp']
            occupied_count = df.iloc[i]['occupied_spaces']

            # Randomly select spaces and create events
            num_events = np.random.randint(1, 5)
            selected_spaces = np.random.choice(spaces, size=num_events, replace=False)

            for space in selected_spaces:
                event_type = 'entry' if np.random.random() < (occupied_count / len(spaces)) else 'exit'
                vehicle_types = ['car', 'suv', 'truck', 'motorcycle']

                event = ParkingEvent(
                    space_number=space.space_number,
                    event_type=event_type,
                    timestamp=timestamp,
                    vehicle_type=np.random.choice(vehicle_types),
                    confidence=np.random.uniform(0.7, 1.0)
                )
                session.add(event)
                event_count += 1

        session.commit()
        print(f"Generated {event_count} parking events")

        # Update current parking space occupancy
        print("Setting current parking space occupancy...")
        latest_occupancy = df.iloc[-1]
        occupied_count = int(latest_occupancy['occupied_spaces'])

        all_spaces = session.query(ParkingSpace).all()
        occupied_spaces = np.random.choice(all_spaces, size=occupied_count, replace=False)

        for space in all_spaces:
            space.is_occupied = space in occupied_spaces
            space.last_updated = datetime.now()

        session.commit()
        print("Current occupancy set")

        print("\n" + "="*50)
        print("Sample data generation complete!")
        print("="*50)

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        raise

    finally:
        session.close()


def train_model_with_sample_data():
    """Train ML model with generated sample data"""
    print("\n" + "="*50)
    print("Training ML Model")
    print("="*50)

    predictor = OccupancyPredictor()

    # Load historical data from database
    print("Loading historical data from database...")
    df = predictor.get_historical_data(days=60)

    if len(df) == 0:
        print("No data available. Generate sample data first.")
        return

    print(f"Loaded {len(df)} records")

    # Train model
    print("\nTraining model...")
    results = predictor.train_model(df)

    print("\n" + "="*50)
    print("Training Results")
    print("="*50)
    print(f"Training Score: {results['train_score']:.4f}")
    print(f"Testing Score: {results['test_score']:.4f}")

    # Save model
    print("\nSaving model...")
    predictor.save_model()

    # Test predictions
    print("\n" + "="*50)
    print("Sample Predictions (Next 6 Hours)")
    print("="*50)

    predictions = predictor.predict_future_occupancy(hours_ahead=6)

    for pred in predictions:
        print(f"{pred['target_time'].strftime('%Y-%m-%d %H:%M')} - "
              f"Predicted: {pred['predicted_occupancy_rate']:.1%} "
              f"({pred['predicted_occupied_spaces']}/{config.PARKING_LOT_CONFIG['total_spaces']} spaces)")

    print("\n" + "="*50)
    print("Model training complete!")
    print("="*50)


def main():
    """Main function"""
    import sys

    if len(sys.argv) > 1:
        days = int(sys.argv[1])
    else:
        days = 60

    print("="*50)
    print("Smart Parking System - Sample Data Generator")
    print("="*50)
    print(f"\nGenerating {days} days of sample data...\n")

    # Generate and populate database
    populate_database_with_sample_data(days)

    # Train model
    train_model_with_sample_data()

    print("\n" + "="*50)
    print("All done! You can now run the application:")
    print("  python app.py")
    print("="*50)


if __name__ == "__main__":
    main()
