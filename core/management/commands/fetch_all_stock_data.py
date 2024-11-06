from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import Issuer
from core.pipeline import Pipeline, IssuerListFilter
from core.management.commands.fetch_stock_data_for_symbol import Command as FetchCommand
import concurrent.futures

class Command(BaseCommand):
    help = 'Fetches historical stock data for all symbols across multiple years'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-year',
            type=int,
            default=2000,
            help='Start year (default: 2000)'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=3,
            help='Number of concurrent workers (default: 3)'
        )

    def handle(self, *args, **options):
        pipeline = Pipeline()
        pipeline.add_filter(IssuerListFilter())
        symbols = pipeline.execute()
        
        current_year = timezone.now().year
        from_year = options['from_year']
        workers = options['workers']

        total_requests = len(symbols) * (current_year - from_year + 1)
        completed = 0

        fetch_command = FetchCommand()

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            
            for symbol in symbols:
                for year in range(from_year, current_year + 1):
                    start_date = datetime(year, 1, 1)
                    end_date = datetime(year, 12, 31)
                    
                    futures.append(
                        executor.submit(
                            fetch_command.handle,
                            symbol=symbol,
                            from_date=start_date.strftime('%Y-%m-%d'),
                            to_date=end_date.strftime('%Y-%m-%d'),
                            quiet=True
                        )
                    )

            for future in concurrent.futures.as_completed(futures):
                completed += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Progress: {completed}/{total_requests} requests completed'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully fetched data for all symbols from {from_year} to {current_year}'
            )
        ) 