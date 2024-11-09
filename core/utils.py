from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import pandas as pd
import time
import queue
import logging

class WebScraper:
    def __init__(self, max_workers=10, headless=True):
        self.max_workers = max_workers
        self.headless = headless
        
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless=new')
        
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument('--disable-infobars')
        self.chrome_options.add_argument('--disable-notifications')
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        prefs = {
            'profile.default_content_setting_values': {
                'notifications': 2,
                'alerts': 2
            }
        }
        self.chrome_options.add_experimental_option('prefs', prefs)
        self.driver_pool = queue.Queue()
        
    def _create_driver(self):
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=self.chrome_options)
    
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
            
            wait.until(lambda driver: driver.find_element(By.ID, "resultsTable") or 
                                    driver.find_element(By.CLASS_NAME, "no-results"))
            time.sleep(1)
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            no_results = soup.find('div', {'class': 'no-results'})
            if no_results and 'No data' in no_results.text:
                logging.debug(f'No data found for {symbol} between {from_date} and {to_date}')
                driver.quit()
                return pd.DataFrame({
                    'date': pd.date_range(from_date, to_date),
                    'last_trade_price': 0,
                    'max_price': 0,
                    'min_price': 0,
                    'avg_price': 0,
                    'price_change': 0,
                    'volume': 0,
                    'turnover_best': 0,
                    'total_turnover': 0
                })
            
            table = soup.find('table', {'id': 'resultsTable'})
            
            headers = [
                'date', 'last_trade_price', 'max_price', 'min_price', 
                'avg_price', 'price_change', 'volume', 'turnover_best', 
                'total_turnover'
            ]
            
            if not table or not table.find('tbody').find_all('tr'):
                date_range = pd.date_range(from_date, to_date)
                df = pd.DataFrame({
                    'date': date_range,
                    'last_trade_price': 0,
                    'max_price': 0,
                    'min_price': 0,
                    'avg_price': 0,
                    'price_change': 0,
                    'volume': 0,
                    'turnover_best': 0,
                    'total_turnover': 0
                })
                df['date'] = df['date'].dt.date
                return df
            
            rows = []
            for tr in table.find('tbody').find_all('tr'):
                row = []
                for td in tr.find_all('td'):
                    value = td.text.strip().replace(',', '')
                    row.append(value)
                rows.append(row)
                
            df = pd.DataFrame(rows, columns=headers)
            
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            numeric_columns = ['last_trade_price', 'max_price', 'min_price', 
                              'avg_price', 'price_change', 'volume', 
                              'turnover_best', 'total_turnover']
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logging.error(f"Error in _fetch_data_chunk: {str(e)}")
            driver.quit()
            raise
        finally:
            try:
                driver.quit()
            except:
                pass
            
    def get_stock_data(self, symbol, from_date, to_date):
        try:
            return self._fetch_data_chunk((symbol, from_date, to_date))
        except Exception as e:
            logging.error(f"Error in get_stock_data: {str(e)}")
            date_range = pd.date_range(from_date, to_date)
            return pd.DataFrame({
                'date': date_range,
                'last_trade_price': 0,
                'max_price': 0,
                'min_price': 0,
                'avg_price': 0,
                'price_change': 0,
                'volume': 0,
                'turnover_best': 0,
                'total_turnover': 0
            })