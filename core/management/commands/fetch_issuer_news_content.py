from django.core.management.base import BaseCommand
from core.models import IssuerNews
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Command(BaseCommand):
    help = 'Fetches content for news items from seinet.com.mk'
    
    def __init__(self):
        super().__init__()
        # Initialize Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Use webdriver_manager to get the correct ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def add_arguments(self, parser):
        parser.add_argument(
            '--empty_only',
            action='store_true',
            help='Only fetch content for news items with empty content'
        )

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        
        try:
            # Get news items that need content
            if options['empty_only']:
                news_items = IssuerNews.objects.filter(content='')
            else:
                news_items = IssuerNews.objects.all()
                
            total = news_items.count()
            logging.info(f"Found {total} news items to process")
            
            for i, news in enumerate(news_items, 1):
                try:
                    self.fetch_content(news, i, total)
                    time.sleep(1)  # Be nice to the server
                except Exception as e:
                    logging.error(f"Error processing news {news.id}: {str(e)}")
        finally:
            self.driver.quit()
    
    def get_text_recursive(self, element):
        """Recursively get text from all nested divs"""
        if not element.find_elements(By.TAG_NAME, 'div'):
            # If no more nested divs, get the text
            text = element.text.strip()
            if text:
                return text
            # Check for links
            links = element.find_elements(By.TAG_NAME, 'a')
            if links:
                return '\n'.join(f"Link: {link.get_attribute('href')}" 
                               for link in links 
                               if link.get_attribute('href') and 
                               not link.get_attribute('href').startswith('#'))
            return None
        
        # If has nested divs, recurse into them
        texts = []
        for div in element.find_elements(By.TAG_NAME, 'div'):
            text = self.get_text_recursive(div)
            if text:
                texts.append(text)
        return '\n'.join(texts) if texts else None

    def fetch_content(self, news, current, total):
        if not news.source_url:
            logging.warning(f"No source URL for news {news.id}")
            return
            
        logging.info(f"Processing {current}/{total}: {news.source_url}")
        
        try:
            self.driver.get(news.source_url)
            wait = WebDriverWait(self.driver, 10)
            
            # Get the root div
            root = wait.until(EC.presence_of_element_located((By.ID, 'root')))
            
            # Find main container
            main = root.find_element(By.CSS_SELECTOR, 'main.main.text-center')
            container = main.find_element(By.CLASS_NAME, 'container')
            
            content_parts = []
            
            # Get content from each row div recursively
            rows = container.find_elements(By.CLASS_NAME, 'row')
            for row in rows:
                text = self.get_text_recursive(row)
                if text:
                    content_parts.append(text)
            
            # Clean and join content
            content = '\n\n'.join(part for part in content_parts if part)
            
            if content:
                news.content = content
                news.save()
                logging.info(f"Updated content for news {news.id} to {content}")
            else:
                logging.warning(f"No content found in {news.source_url}")
                
        except Exception as e:
            logging.error(f"Error processing {news.source_url}: {str(e)}")
            return 