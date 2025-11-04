import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
import joblib
from typing import List, Dict
import config
from database import get_session, OccupancyHistory


class OccupancyPredictor:
    """Machine Learning model for predicting parking lot occupancy"""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = config.MODEL_CONFIG['input_features']

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for training/prediction"""
        df = df.copy()

        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Extract time-based features
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['month'] = df['timestamp'].dt.month
            df['day_of_month'] = df['timestamp'].dt.day

        # Calculate rolling averages
        if 'occupancy_rate' in df.columns:
            df['avg_occupancy_last_hour'] = df['occupancy_rate'].rolling(
                window=12, min_periods=1
            ).mean()

            df['avg_occupancy_last_3_hours'] = df['occupancy_rate'].rolling(
                window=36, min_periods=1
            ).mean()

            # Weekly patterns
            df['avg_occupancy_same_hour_last_week'] = df.groupby('hour')['occupancy_rate'].transform(
                lambda x: x.shift(7 * 24 * 12).fillna(x.mean())
            )

        # Current occupancy
        if 'occupied_spaces' in df.columns:
            df['current_occupancy'] = df['occupied_spaces']

        return df

    def train_model(self, data: pd.DataFrame):
        """Train the occupancy prediction model"""
        print("Preparing training data...")

        # Prepare features
        df = self.prepare_features(data)

        # Select features
        available_features = [f for f in self.feature_columns if f in df.columns]

        if len(available_features) == 0:
            raise ValueError("No valid features found in the data")

        X = df[available_features].fillna(0)
        y = df['occupancy_rate'] if 'occupancy_rate' in df.columns else df['occupied_spaces']

        # Remove any remaining NaN values
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]

        print(f"Training with {len(X)} samples and {len(available_features)} features")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train ensemble model
        print("Training Random Forest model...")
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train_scaled, y_train)

        print("Training Gradient Boosting model...")
        gb_model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        gb_model.fit(X_train_scaled, y_train)

        # Use the better performing model
        rf_score = rf_model.score(X_test_scaled, y_test)
        gb_score = gb_model.score(X_test_scaled, y_test)

        print(f"Random Forest R² Score: {rf_score:.4f}")
        print(f"Gradient Boosting R² Score: {gb_score:.4f}")

        if rf_score > gb_score:
            self.model = rf_model
            print("Selected Random Forest model")
        else:
            self.model = gb_model
            print("Selected Gradient Boosting model")

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': available_features,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        print("\nFeature Importance:")
        print(feature_importance)

        return {
            'train_score': self.model.score(X_train_scaled, y_train),
            'test_score': self.model.score(X_test_scaled, y_test),
            'feature_importance': feature_importance.to_dict('records')
        }

    def predict(self, features: Dict) -> float:
        """Predict occupancy for given features"""
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained or loaded")

        # Create DataFrame from features
        df = pd.DataFrame([features])

        # Ensure all required features are present
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0

        # Select and order features
        X = df[self.feature_columns]

        # Scale features
        X_scaled = self.scaler.transform(X)

        # Predict
        prediction = self.model.predict(X_scaled)[0]

        # Ensure prediction is within valid range (0-1 for occupancy rate)
        prediction = max(0, min(1, prediction))

        return prediction

    def predict_future_occupancy(
        self, hours_ahead: int = 6, current_data: Dict = None
    ) -> List[Dict]:
        """Predict occupancy for the next N hours"""
        predictions = []
        now = datetime.now()

        for hour_offset in range(1, hours_ahead + 1):
            target_time = now + timedelta(hours=hour_offset)

            features = {
                'hour': target_time.hour,
                'day_of_week': target_time.weekday(),
                'is_weekend': 1 if target_time.weekday() >= 5 else 0,
            }

            # Add current data if available
            if current_data:
                features.update(current_data)

            # Predict
            predicted_occupancy = self.predict(features)

            predictions.append({
                'target_time': target_time,
                'predicted_occupancy_rate': predicted_occupancy,
                'predicted_occupied_spaces': int(
                    predicted_occupancy * config.PARKING_LOT_CONFIG['total_spaces']
                ),
                'predicted_available_spaces': int(
                    (1 - predicted_occupancy) * config.PARKING_LOT_CONFIG['total_spaces']
                )
            })

        return predictions

    def save_model(self):
        """Save trained model and scaler"""
        if self.model is None or self.scaler is None:
            raise ValueError("No model to save")

        model_path = config.MODEL_CONFIG['model_path']
        scaler_path = config.MODEL_CONFIG['scaler_path']

        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)

        print(f"Model saved to {model_path}")
        print(f"Scaler saved to {scaler_path}")

    def load_model(self):
        """Load trained model and scaler"""
        model_path = config.MODEL_CONFIG['model_path']
        scaler_path = config.MODEL_CONFIG['scaler_path']

        if not model_path.exists() or not scaler_path.exists():
            raise FileNotFoundError("Model files not found. Train the model first.")

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)

        print("Model and scaler loaded successfully")

    def get_historical_data(self, days: int = 30) -> pd.DataFrame:
        """Get historical occupancy data from database"""
        session = get_session()

        cutoff_date = datetime.now() - timedelta(days=days)

        history = session.query(OccupancyHistory).filter(
            OccupancyHistory.timestamp >= cutoff_date
        ).all()

        session.close()

        if not history:
            return pd.DataFrame()

        data = [{
            'timestamp': h.timestamp,
            'occupied_spaces': h.occupied_spaces,
            'available_spaces': h.available_spaces,
            'occupancy_rate': h.occupancy_rate
        } for h in history]

        return pd.DataFrame(data)


if __name__ == "__main__":
    # Example usage
    predictor = OccupancyPredictor()

    # Try to load existing data
    print("Loading historical data...")
    df = predictor.get_historical_data(days=30)

    if len(df) > 0:
        print(f"Loaded {len(df)} records")
        print("\nTraining model...")
        results = predictor.train_model(df)
        print("\nTraining completed!")
        print(f"Train Score: {results['train_score']:.4f}")
        print(f"Test Score: {results['test_score']:.4f}")

        # Save model
        predictor.save_model()

        # Test prediction
        print("\nPredicting future occupancy...")
        predictions = predictor.predict_future_occupancy(hours_ahead=6)
        for pred in predictions:
            print(f"{pred['target_time'].strftime('%Y-%m-%d %H:%M')} - "
                  f"Occupancy: {pred['predicted_occupancy_rate']:.2%} "
                  f"({pred['predicted_occupied_spaces']}/{config.PARKING_LOT_CONFIG['total_spaces']})")
    else:
        print("No historical data available. Generate sample data first.")
