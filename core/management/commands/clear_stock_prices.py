from django.core.management.base import BaseCommand
from core.models import StockPrice
import time

class Command(BaseCommand):
    help = 'Clears all stock price records from the database'

    def handle(self, *args, **options):
        start_time = time.time()
        
        self.stdout.write(self.style.WARNING('Clearing all stock price records...'))
        
        count = StockPrice.objects.count()
        StockPrice.objects.all().delete()
        
        duration = time.time() - start_time
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {count:,} records in {duration:.2f} seconds'
            )
        ) 