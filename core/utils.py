from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import time
import queue
import threading

class WebScraper:
    def __init__(self, max_workers=4):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument("--headless")
        self.max_workers = max_workers
        self.driver_pool = queue.Queue()
        
    def _create_driver(self):
        return webdriver.Chrome(options=self.chrome_options)
    
    def _get_driver(self):
        try:
            driver = self.driver_pool.get_nowait()
        except queue.Empty:
            driver = self._create_driver()
        return driver
    
    def _return_driver(self, driver):
        self.driver_pool.put(driver)
        
    def get_symbols(self):
        driver = self._get_driver()
        try:
            driver.get("https://www.mse.mk/en/stats/symbolhistory/TEL")
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.ID, "Code")))
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            symbol_select = soup.find('select', {'id': 'Code'})
            
            symbols = []
            if symbol_select:
                for option in symbol_select.find_all('option'):
                    symbol = option['value']
                    if not any(char.isdigit() for char in symbol):
                        symbols.append({
                            'symbol': symbol,
                            'name': option.text
                        })
            return symbols
            
        finally:
            self._return_driver(driver)
            
    def _fetch_data_chunk(self, args):
        symbol, from_date, to_date = args
        driver = self._get_driver()
        try:
            driver.get("https://www.mse.mk/en/stats/symbolhistory/TEL")
            wait = WebDriverWait(driver, 10)
            
            from_date_input = wait.until(EC.presence_of_element_located((By.ID, "FromDate")))
            from_date_input.clear()
            from_date_input.send_keys(from_date.strftime('%-m/%-d/%Y'))
            
            to_date_input = driver.find_element(By.ID, "ToDate")
            to_date_input.clear()
            to_date_input.send_keys(to_date.strftime('%-m/%-d/%Y'))
            
            dropdown = wait.until(EC.presence_of_element_located((By.ID, "Code")))
            select = Select(dropdown)
            select.select_by_value(symbol)
            
            find_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Find']")
            find_button.click()
            
            wait.until(EC.presence_of_element_located((By.ID, "resultsTable")))
            time.sleep(1)
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', {'id': 'resultsTable'})
            
            headers = []
            for th in table.find('thead').find_all('th'):
                headers.append(th.text.strip())
                
            rows = []
            for tr in table.find('tbody').find_all('tr'):
                row = []
                for td in tr.find_all('td'):
                    row.append(td.text.strip())
                rows.append(row)
                
            return pd.DataFrame(rows, columns=headers)
            
        finally:
            self._return_driver(driver)
            
    def get_stock_data(self, symbol, from_date, to_date, chunk_size=30):
        chunks = []
        current_date = from_date
        while current_date < to_date:
            chunk_end = min(current_date + pd.Timedelta(days=chunk_size), to_date)
            chunks.append((symbol, current_date, chunk_end))
            current_date = chunk_end + pd.Timedelta(days=1)
        
        all_data = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._fetch_data_chunk, chunk) for chunk in chunks]
            
            for future in as_completed(futures):
                try:
                    df = future.result()
                    if not df.empty:
                        all_data.append(df)
                except Exception as e:
                    print(f"Error fetching chunk: {str(e)}")
        
        # combine all chunks
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()