from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Issuer
import pandas as pd
import logging

class Command(BaseCommand):
    help = 'Updates Issuer model names from issuer_ids.csv'

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        
        # Read the CSV
        df = pd.read_csv('data/issuer_ids.csv')
        
        # Create a mapping of symbol to name
        symbol_to_name = {}
        for _, row in df.iterrows():
            if pd.notna(row['symbols']) and row['symbols']:
                symbols = row['symbols'].split(',')
                name = row['data_name'].replace('-', ' ')  # Convert hyphens to spaces
                for symbol in symbols:
                    symbol_to_name[symbol.strip()] = name
        
        # Update Issuer models
        total_updated = 0
        for issuer in Issuer.objects.all():
            if issuer.code in symbol_to_name:
                name = symbol_to_name[issuer.code]
                if issuer.name != name:
                    logging.info(f"Updating {issuer.code}: {issuer.name} -> {name}")
                    issuer.name = name
                    issuer.last_updated = timezone.now()
                    issuer.save()
                    total_updated += 1
            else:
                logging.warning(f"No name found for symbol: {issuer.code}")
        
        logging.info(f"Updated {total_updated} issuer names")