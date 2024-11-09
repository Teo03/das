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
            help='Start date in format YYYY-MM-DD or MM/DD/YYYY',
            required=True
        )
        parser.add_argument(
            '--to-date',
            type=str,
            help='End date in format YYYY-MM-DD or MM/DD/YYYY',
            required=True
        )
        parser.add_argument('--quiet', action='store_true', help='Suppress output')
        parser.add_argument(
            '--return-data',
            action='store_true',
            help='Return data instead of saving to database'
        )
        parser.add_argument(
            '--no-db-save',
            action='store_true',
            help='Do not save data to database'
        )

    def handle(self, *args, **options):
        try:
            issuer = Issuer.objects.get(code=options['symbol'])
            
            from_date_str = options['from_date']
            to_date_str = options['to_date']
            
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            except ValueError:
                from_date = datetime.strptime(from_date_str, '%m/%d/%Y').date()
                to_date = datetime.strptime(to_date_str, '%m/%d/%Y').date()
            
            input_data = {
                'symbol': options['symbol'],
                'issuer': issuer,
                'from_date': from_date,
                'to_date': to_date
            }
            
            pipeline = Pipeline()
            pipeline.add_filter(DataFetchFilter(save_to_db=not options.get('no_db_save', False)))
            
            result = pipeline.execute(input_data)
            
            if not options.get('quiet'):
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully fetched data for {options["symbol"]}\n'
                        f'From: {from_date} To: {to_date}'
                    )
                )
            
            if options.get('return_data'):
                return result
            
        except Issuer.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Symbol {options["symbol"]} not found in database. Run get_all_symbols first.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error in pipeline execution: {str(e)}')
            )