import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
import joblib
import os
from django.conf import settings

class TimeSeriesPredictor:
    def __init__(self, sequence_length=10):
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = MLPRegressor(
            hidden_layer_sizes=(100, 50),
            activation='relu',
            solver='adam',
            learning_rate='adaptive',
            max_iter=200,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=10
        )
        
    def prepare_data(self, data):
        # Scale the data
        scaled_data = self.scaler.fit_transform(data.reshape(-1, 1))
        
        X, y = [], []
        for i in range(len(scaled_data) - self.sequence_length):
            X.append(scaled_data[i:(i + self.sequence_length), 0])
            y.append(scaled_data[i + self.sequence_length, 0])
        
        X = np.array(X)
        y = np.array(y)
        return X, y
        
    def train(self, data, validation_split=0.3):
        # Prepare data
        X, y = self.prepare_data(data)
        
        # Split data into training and validation sets
        train_size = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:train_size], X[train_size:]
        y_train, y_val = y[:train_size], y[train_size:]
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Calculate metrics
        train_predictions = self.model.predict(X_train)
        val_predictions = self.model.predict(X_val)
        
        # Inverse transform predictions
        train_predictions = self.scaler.inverse_transform(train_predictions.reshape(-1, 1))
        y_train_inv = self.scaler.inverse_transform(y_train.reshape(-1, 1))
        val_predictions = self.scaler.inverse_transform(val_predictions.reshape(-1, 1))
        y_val_inv = self.scaler.inverse_transform(y_val.reshape(-1, 1))
        
        # Calculate error metrics
        train_rmse = np.sqrt(mean_squared_error(y_train_inv, train_predictions))
        val_rmse = np.sqrt(mean_squared_error(y_val_inv, val_predictions))
        train_mae = mean_absolute_error(y_train_inv, train_predictions)
        val_mae = mean_absolute_error(y_val_inv, val_predictions)
        
        # Get loss curve
        loss_curve = self.model.loss_curve_ if hasattr(self.model, 'loss_curve_') else []
        validation_scores = self.model.validation_scores_ if hasattr(self.model, 'validation_scores_') else []
        
        return {
            'history': {
                'loss': loss_curve,
                'val_loss': validation_scores
            },
            'metrics': {
                'train_rmse': train_rmse,
                'val_rmse': val_rmse,
                'train_mae': train_mae,
                'val_mae': val_mae
            }
        }

class PricePredictor:
    def __init__(self, symbol, sequence_length=10):
        self.symbol = symbol
        self.sequence_length = sequence_length
        self.models_dir = os.path.join(settings.BASE_DIR, 'trained_models')
        
        # Load saved model and scaler
        model_path = os.path.join(self.models_dir, f'{symbol}_model.joblib')
        scaler_path = os.path.join(self.models_dir, f'{symbol}_scaler.joblib')
        metrics_path = os.path.join(self.models_dir, f'{symbol}_metrics.joblib')
        
        if not (os.path.exists(model_path) and os.path.exists(scaler_path)):
            raise FileNotFoundError(f"No trained model found for {symbol}")
        
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.metrics = joblib.load(metrics_path)
    
    def predict_future(self, data, days_ahead=30):
        # Scale the data
        scaled_data = self.scaler.transform(data.reshape(-1, 1))
        
        # Prepare the last sequence
        last_sequence = scaled_data[-self.sequence_length:]
        current_sequence = last_sequence.reshape(1, -1)
        
        # Make predictions
        predictions = []
        for _ in range(days_ahead):
            # Get prediction
            next_pred = self.model.predict(current_sequence)[0]
            predictions.append(next_pred)
            
            # Update sequence
            current_sequence = np.roll(current_sequence, -1)
            current_sequence[0, -1] = next_pred
        
        # Inverse transform predictions
        predictions = np.array(predictions).reshape(-1, 1)
        predictions = self.scaler.inverse_transform(predictions)
        
        return predictions.flatten()

    def generate_plots(self, data, predictions):
        # Create figure with subplots
        fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))
        
        # Plot: Actual vs Predicted
        ax1.plot(data[-len(predictions):], label='Actual', color='blue')
        ax1.plot(predictions, label='Predicted', color='red')
        ax1.set_title('Price Prediction')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True)
        
        # Adjust layout and convert to base64
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode()

def prepare_prediction(symbol, stock_prices, days_ahead=30):
    try:
        # Convert prices to numpy array
        prices = np.array([float(price) for price in stock_prices])
        
        # Initialize predictor with saved model
        predictor = PricePredictor(symbol)
        
        # Make future predictions
        future_predictions = predictor.predict_future(prices, days_ahead)
        
        # Generate plots
        plots_base64 = predictor.generate_plots(prices, future_predictions)
        
        return {
            'predictions': future_predictions.tolist(),
            'metrics': predictor.metrics,
            'plots': plots_base64
        }
    except FileNotFoundError:
        return None 