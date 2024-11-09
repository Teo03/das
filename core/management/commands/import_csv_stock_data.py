from django.core.management.base import BaseCommand
from core.models import Issuer, StockPrice
from decimal import Decimal
import pandas as pd
import os
import glob
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import transaction
import multiprocessing

class Command(BaseCommand):
    help = 'Imports stock data from CSV files in stock_data folder into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threads',
            type=int,
            default=multiprocessing.cpu_count(),
            help='Number of threads to use (default: number of CPU cores)'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        
        csv_dir = 'stock_data'
        if not os.path.exists(csv_dir):
            self.stdout.write(self.style.ERROR(f'"{csv_dir}" directory not found!'))
            return

        csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))
        if not csv_files:
            self.stdout.write(self.style.ERROR('No CSV files found in stock_data directory!'))
            return

        self.stdout.write(f'Found {len(csv_files)} CSV files to process')

        # Preload all Issuers into a dictionary for quick access
        issuers = {issuer.code: issuer for issuer in Issuer.objects.all()}
        if not issuers:
            self.stdout.write(self.style.ERROR('No issuers found in the database!'))
            return

        total_records = 0
        processed_files = 0
        threads = options['threads']
        self.stdout.write(f'Using {threads} threads for processing')

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [
                executor.submit(self._process_file, filepath, issuers)
                for filepath in csv_files
            ]
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    symbol, year, record_count = result
                    total_records += record_count
                    processed_files += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Processed {symbol} {year}: {record_count} records '
                            f'({processed_files}/{len(csv_files)} files)'
                        )
                    )

        duration = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed in {duration:.2f} seconds\n'
                f'Total files processed: {processed_files}\n'
                f'Total records imported: {total_records}'
            )
        )

    def _process_file(self, filepath, issuers):
        try:
            filename = os.path.basename(filepath)
            symbol, year = filename.replace('.csv', '').split('_')
            
            issuer = issuers.get(symbol)
            if not issuer:
                self.stdout.write(
                    self.style.ERROR(f'Issuer "{symbol}" not found!')
                )
                return None

            df = pd.read_csv(filepath, usecols=[
                'date', 'last_trade_price', 'max_price', 'min_price',
                'avg_price', 'price_change', 'volume', 'turnover_best', 'total_turnover'
            ])
            df.dropna(subset=['date'], inplace=True)

            df.fillna({
                'last_trade_price': 0,
                'max_price': 0,
                'min_price': 0,
                'avg_price': 0,
                'price_change': 0,
                'volume': 0,
                'turnover_best': 0,
                'total_turnover': 0
            }, inplace=True)

            df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d').dt.date
            df['last_trade_price'] = df['last_trade_price'].astype(float)
            df['max_price'] = df['max_price'].astype(float)
            df['min_price'] = df['min_price'].astype(float)
            df['avg_price'] = df['avg_price'].astype(float)
            df['price_change'] = df['price_change'].astype(float)
            df['volume'] = df['volume'].astype(int)
            df['turnover_best'] = df['turnover_best'].astype(float)
            df['total_turnover'] = df['total_turnover'].astype(float)

            stock_prices = [
                StockPrice(
                    issuer=issuer,
                    date=row['date'],
                    last_trade_price=Decimal(f"{row['last_trade_price']:.2f}"),
                    max_price=Decimal(f"{row['max_price']:.2f}"),
                    min_price=Decimal(f"{row['min_price']:.2f}"),
                    avg_price=Decimal(f"{row['avg_price']:.2f}"),
                    price_change=Decimal(f"{row['price_change']:.2f}"),
                    volume=row['volume'],
                    turnover_best=Decimal(f"{row['turnover_best']:.2f}"),
                    total_turnover=Decimal(f"{row['total_turnover']:.2f}")
                )
                for _, row in df.iterrows()
            ]

            with transaction.atomic():
                StockPrice.objects.bulk_create(
                    stock_prices,
                    ignore_conflicts=True,
                    batch_size=50000
                )
            
            return symbol, year, len(stock_prices)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing {filepath}: {str(e)}')
            )
            return None