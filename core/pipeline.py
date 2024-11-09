from abc import ABC, abstractmethod
from typing import Any
from .models import Issuer, StockPrice
from .utils import WebScraper
from decimal import Decimal
import pandas as pd
import time

class Filter(ABC):
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        pass

class IssuerListFilter(Filter):
    def process(self, input_data=None):
        scraper = WebScraper(headless=True)
        symbols = scraper.get_symbols()
        
        # create or update issuers in database, excluding symbols starting with 'E'
        filtered_symbols = []
        for symbol_data in symbols:
            if not symbol_data['symbol'].startswith('E'):
                Issuer.objects.update_or_create(
                    code=symbol_data['symbol'],
                    defaults={'name': symbol_data['name']}
                )
                filtered_symbols.append(symbol_data['symbol'])
        
        return filtered_symbols

class DataFetchFilter(Filter):
    def __init__(self, max_workers=10, save_to_db=True):
        self.max_workers = max_workers
        self.scraper = WebScraper(max_workers=max_workers, headless=True)
        self.save_to_db = save_to_db
    
    def _save_stock_data(self, df, issuer):
        if not self.save_to_db:
            return
            
        # Rename columns to match our model fields
        column_mapping = {
            'last trade price': 'last_trade_price',
            'avg. price': 'avg_price',
            '%chg.': 'price_change',
            'turnover in best in denars': 'turnover_best',
            'total turnover in denars': 'total_turnover'
        }
        df = df.rename(columns=column_mapping)
        
        for _, row in df.iterrows():
            try:
                defaults = {}
                fields = {
                    'last_trade_price': lambda x: Decimal(str(x)) if pd.notna(x) else Decimal('0'),
                    'max_price': lambda x: Decimal(str(x)) if pd.notna(x) else Decimal('0'),
                    'min_price': lambda x: Decimal(str(x)) if pd.notna(x) else Decimal('0'),
                    'avg_price': lambda x: Decimal(str(x)) if pd.notna(x) else Decimal('0'),
                    'price_change': lambda x: Decimal(str(x)) if pd.notna(x) else Decimal('0'),
                    'volume': lambda x: int(float(x)) if pd.notna(x) else 0,
                    'turnover_best': lambda x: Decimal(str(x)) if pd.notna(x) else Decimal('0'),
                    'total_turnover': lambda x: Decimal(str(x)) if pd.notna(x) else Decimal('0')
                }
                
                for field, converter in fields.items():
                    try:
                        value = row.get(field)
                        if isinstance(value, str):
                            value = value.replace(',', '')
                        defaults[field] = converter(value)
                    except (ValueError, TypeError, KeyError) as e:
                        print(f"Error converting {field}: {value} - {str(e)}")
                        defaults[field] = Decimal('0') if field != 'volume' else 0

                StockPrice.objects.update_or_create(
                    issuer=issuer,
                    date=row['date'],
                    defaults=defaults
                )
            except Exception as e:
                print(f"Error saving row {row.get('date', 'unknown date')}: {str(e)}")
                print(f"Row data: {row.to_dict()}")
                continue
    
    def process(self, input_data):
        if not input_data:
            return []
        
        df = self.scraper.get_stock_data(
            input_data['symbol'], 
            input_data['from_date'],
            input_data['to_date']
        )
        
        if not df.empty:
            self._save_stock_data(df, input_data['issuer'])
            return df.to_dict('records')
        return []

class Pipeline:
    def __init__(self):
        self.filters = []
        self.start_time = None

    def add_filter(self, filter: Filter):
        self.filters.append(filter)

    def execute(self, input_data=None):
        self.start_time = time.time()
        data = input_data
        for filter in self.filters:
            data = filter.process(data)
        execution_time = time.time() - self.start_time
        print(f"Pipeline executed in {execution_time:.2f} seconds")
        return data