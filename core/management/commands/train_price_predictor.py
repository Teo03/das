from django.core.management.base import BaseCommand
from core.models import Issuer, StockPrice
from core.lstm_prediction import TimeSeriesPredictor
import numpy as np
import joblib
import os
from datetime import datetime, timedelta
from django.conf import settings

class Command(BaseCommand):
    help = 'Train price prediction models for all stocks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Stock symbol to train model for. If not provided, trains for all stocks.',
        )

    def handle(self, *args, **options):
        # Create models directory if it doesn't exist
        models_dir = os.path.join(settings.BASE_DIR, 'trained_models')
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)

        if options['symbol']:
            issuers = Issuer.objects.filter(code=options['symbol'])
        else:
            issuers = Issuer.objects.all()

        for issuer in issuers:
            self.stdout.write(f"Training model for {issuer.code}...")
            
            # Get historical prices
            historical_prices = StockPrice.objects.filter(
                issuer=issuer
            ).order_by('date').values_list('last_trade_price', flat=True)
            
            if len(historical_prices) <= 30:
                self.stdout.write(self.style.WARNING(
                    f"Skipping {issuer.code}: Not enough data (need >30 days, got {len(historical_prices)})"
                ))
                continue

            try:
                # Convert to numpy array
                prices = np.array([float(price) for price in historical_prices])
                
                # Initialize and train predictor
                predictor = TimeSeriesPredictor(sequence_length=10)
                training_results = predictor.train(prices)
                
                # Save the trained model and scaler
                model_path = os.path.join(models_dir, f'{issuer.code}_model.joblib')
                scaler_path = os.path.join(models_dir, f'{issuer.code}_scaler.joblib')
                
                joblib.dump(predictor.model, model_path)
                joblib.dump(predictor.scaler, scaler_path)
                
                # Save training metrics
                metrics_path = os.path.join(models_dir, f'{issuer.code}_metrics.joblib')
                joblib.dump(training_results['metrics'], metrics_path)
                
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully trained model for {issuer.code} - "
                    f"Train RMSE: {training_results['metrics']['train_rmse']:.2f}, "
                    f"Val RMSE: {training_results['metrics']['val_rmse']:.2f}"
                ))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error training model for {issuer.code}: {str(e)}"
                ))
                continue 