from django.core.management.base import BaseCommand
from core.pipeline import Pipeline, DataFetchFilter
from core.models import Issuer
from datetime import datetime

class Command(BaseCommand):
    help = 'Fetches stock market data for a specific symbol and date range'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Symbol to fetch data for',
            required=True
        )
        parser.add_argument(
            '--from-date',
            type=str,
            help='Start date in format YYYY-MM-DD',
            required=True
        )
        parser.add_argument(
            '--to-date',
            type=str,
            help='End date in format YYYY-MM-DD',
            required=True
        )

    def handle(self, *args, **options):
        try:
            issuer = Issuer.objects.get(code=options['symbol'])
            
            from_date = datetime.strptime(options['from_date'], '%Y-%m-%d').date()
            to_date = datetime.strptime(options['to_date'], '%Y-%m-%d').date()
            
            input_data = {
                options['symbol']: {
                    'issuer': issuer,
                    'last_date': from_date
                }
            }
            
            pipeline = Pipeline()
            pipeline.add_filter(DataFetchFilter())
            
            result = pipeline.execute(input_data)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully fetched data for {options["symbol"]}\n'
                    f'From: {from_date} To: {to_date}'
                )
            )
            
        except Issuer.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Symbol {options["symbol"]} not found in database. Run get_all_symbols first.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error in pipeline execution: {str(e)}')
            )