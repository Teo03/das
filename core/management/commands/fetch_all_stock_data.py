from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from core.pipeline import Pipeline, IssuerListFilter
from core.management.commands.fetch_stock_data_for_symbol import Command as FetchCommand
import pandas as pd
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

class Command(BaseCommand):
    help = 'Fetches historical stock data for all symbols and saves yearly CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-year',
            type=int,
            default=2014,
            help='Start year (default: 2014)'
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug logging'
        )

    def handle(self, *args, **options):
        if options['debug']:
            logging.basicConfig(level=logging.DEBUG)
        
        os.makedirs('stock_data', exist_ok=True)
        
        self.stdout.write(self.style.WARNING('Fetching symbol list...'))
        pipeline = Pipeline()
        pipeline.add_filter(IssuerListFilter())
        symbols = pipeline.execute()
        
        if not symbols:
            self.stdout.write(self.style.ERROR('No symbols found!'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {len(symbols)} symbols'))
        
        from_year = options['from_year']
        to_year = 2024
        
        completed_symbols = set()
        total_symbols = len(symbols)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for symbol in symbols:
                for year in range(from_year, to_year + 1):
                    filename = f'stock_data/{symbol}_{year}.csv'
                    if os.path.exists(filename):
                        logging.debug(f'Skipping {filename} - already exists')
                        continue
                    
                    futures.append(executor.submit(
                        self._process_year,
                        symbol=symbol,
                        year=year
                    ))
            
            for future in as_completed(futures):
                try:
                    symbol, year, success = future.result()
                    completed_symbols.add(symbol)
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Completed {symbol} for {year} ({len(completed_symbols)}/{total_symbols} symbols)'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'No data for {symbol} in {year} ({len(completed_symbols)}/{total_symbols} symbols)'
                            )
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed processing: {str(e)}')
                    )

    def _process_year(self, symbol, year):
        try:
            fetch_command = FetchCommand()
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            
            logging.debug(f'Fetching {symbol} for {year}')
            
            data = fetch_command.handle(
                symbol=symbol,
                from_date=start_date.strftime('%Y-%m-%d'),
                to_date=end_date.strftime('%Y-%m-%d'),
                quiet=True,
                return_data=True,
                no_db_save=True
            )
            
            if data:
                df = pd.DataFrame(data)
                if not df.empty:
                    filename = f'stock_data/{symbol}_{year}.csv'
                    df.to_csv(filename, index=False)
                    logging.debug(f'Saved {filename}')
                    return symbol, year, True
            
            return symbol, year, False
                
        except Exception as e:
            logging.error(f'Error processing {symbol} for {year}: {str(e)}')
            raise