from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime, timedelta
from .models import Issuer, StockPrice
from .utils import WebScraper
from decimal import Decimal
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class Filter(ABC):
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        pass

class IssuerListFilter(Filter):
    def process(self, input_data=None):
        scraper = WebScraper()
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
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.scraper = WebScraper(max_workers=max_workers)
    
    def _process_issuer(self, data):
        code, issuer_data = data
        issuer = issuer_data['issuer']
        from_date = issuer_data['last_date']
        to_date = datetime.now().date()
        
        try:
            df = self.scraper.get_stock_data(code, from_date, to_date)
            if not df.empty:
                self._save_stock_data(df, issuer)
                issuer.last_updated = datetime.now()
                issuer.save()
            return code, True
        except Exception as e:
            print(f"Error processing {code}: {str(e)}")
            return code, False
    
    def process(self, issuer_data):
        if not issuer_data:
            return []
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._process_issuer, (code, data)) 
                for code, data in issuer_data.items()
            ]
            
            for future in as_completed(futures):
                try:
                    code, success = future.result()
                    results.append(code)
                except Exception as e:
                    print(f"Error in thread: {str(e)}")
        
        return results

    def _save_stock_data(self, df, issuer):
        batch = []
        for _, row in df.iterrows():
            date = datetime.strptime(row['Date'], '%m/%d/%Y').date()
            
            if row['Volume'] == '0':
                continue
                
            last_trade_price = Decimal(row['Last trade price'].replace(',', ''))
            max_price = Decimal(row['Max'].replace(',', '') if row['Max'] else last_trade_price)
            min_price = Decimal(row['Min'].replace(',', '') if row['Min'] else last_trade_price)
            avg_price = Decimal(row['Avg. Price'].replace(',', '') if row['Avg. Price'] else last_trade_price)
            price_change = Decimal(row['%chg.'].replace(',', ''))
            volume = int(row['Volume'].replace(',', ''))
            turnover_best = Decimal(row['Turnover in BEST in denars'].replace(',', ''))
            total_turnover = Decimal(row['Total turnover in denars'].replace(',', ''))
            
            stock_price = StockPrice(
                issuer=issuer,
                date=date,
                last_trade_price=last_trade_price,
                max_price=max_price,
                min_price=min_price,
                avg_price=avg_price,
                price_change=price_change,
                volume=volume,
                turnover_best=turnover_best,
                total_turnover=total_turnover
            )
            batch.append(stock_price)
            
            if len(batch) >= 100:
                StockPrice.objects.bulk_create(
                    batch, 
                    update_conflicts=True,
                    unique_fields=['issuer', 'date'],
                    update_fields=['last_trade_price', 'max_price', 'min_price', 
                                 'avg_price', 'price_change', 'volume', 
                                 'turnover_best', 'total_turnover']
                )
                batch = []
        
        if batch:
            StockPrice.objects.bulk_create(
                batch,
                update_conflicts=True,
                unique_fields=['issuer', 'date'],
                update_fields=['last_trade_price', 'max_price', 'min_price', 
                             'avg_price', 'price_change', 'volume', 
                             'turnover_best', 'total_turnover']
            )

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