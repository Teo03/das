from django.core.management.base import BaseCommand
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import logging
import csv

class Command(BaseCommand):
    help = 'Scrapes symbol IDs from MSE website and updates issuer_ids.csv'

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        
        # Read raw data first to check for issues
        with open('data/issuer_ids.csv', 'r') as f:
            lines = f.readlines()
            
        # Clean lines and ensure single column
        cleaned_lines = []
        for line in lines:
            parts = line.strip().split(',')
            cleaned_lines.append(parts[0])  # Take only first column
            
        # Write cleaned data
        with open('data/issuer_ids_cleaned.csv', 'w') as f:
            f.write('data_name\n')  # Header
            for line in cleaned_lines[1:]:  # Skip header
                f.write(f"{line}\n")
        
        # Now read the cleaned CSV
        df = pd.read_csv('data/issuer_ids_cleaned.csv')
        
        def get_symbols(issuer_id):
            url = f'https://www.mse.mk/en/issuer/{issuer_id}'
            try:
                response = requests.get(url)
                if response.status_code == 500:
                    logging.error(f"500 error for {issuer_id}")
                    return None
                    
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                symbols_ul = soup.find('ul', {'class': 'nav nav-tabs', 'id': 'symbols'})
                if not symbols_ul:
                    logging.info(f"No symbols found for {issuer_id}")
                    return ''
                
                symbols = []
                for li in symbols_ul.find_all('li', {'class': 'nav-item'}):
                    a_tag = li.find('a')
                    if a_tag:
                        symbol = a_tag.text.strip()
                        symbols.append(symbol)
                
                result = ','.join(symbols)
                logging.info(f"Found symbols for {issuer_id}: {result}")
                return result
            except Exception as e:
                logging.error(f"Error processing {issuer_id}: {str(e)}")
                return None

        # Add new column for symbols
        df['symbols'] = ''

        total = len(df)
        successful_updates = 0
        
        for idx, row in df.iterrows():
            issuer_id = row['data_name']
            logging.info(f"Processing {idx + 1}/{total}: {issuer_id}")
            
            symbols = get_symbols(issuer_id)
            if symbols is not None:
                df.at[idx, 'symbols'] = symbols
                successful_updates += 1
            
            # Sleep to avoid overwhelming the server
            time.sleep(1)

        if successful_updates > 0:
            # Save with both columns only if we had successful updates
            df.to_csv('data/issuer_ids.csv', index=False)
            logging.info(f"Finished updating issuer_ids.csv with {successful_updates} successful updates")
        else:
            logging.error("No successful updates, CSV not saved") 