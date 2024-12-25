from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from core.models import Issuer, IssuerNews
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import time

class Command(BaseCommand):
    help = 'Fetches latest news for issuers from MSE website'

    def add_arguments(self, parser):
        parser.add_argument(
            '--issuer',
            help='Specific issuer code to fetch news for'
        )

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        
        if options['issuer']:
            issuers = Issuer.objects.filter(code=options['issuer'])
        else:
            issuers = Issuer.objects.all()
            
        for issuer in issuers:
            try:
                self.fetch_news_for_issuer(issuer)
                time.sleep(1)  # Be nice to the server
            except Exception as e:
                logging.error(f"Error processing {issuer.code}: {str(e)}")

    def fetch_news_for_issuer(self, issuer):
        # Convert issuer name to URL format
        issuer_url_name = issuer.name.replace(' ', '-')
        url = f'https://www.mse.mk/en/issuer/{issuer_url_name}'
        
        logging.info(f"Fetching news for {issuer.code} from {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_div = soup.find('div', {'id': 'seiNetIssuerLatestNews'})
            if not news_div:
                logging.warning(f"No news section found for {issuer.code}")
                return
                
            news_items = news_div.find_all('li')
            for item in news_items:
                try:
                    news_link = item.find('a')
                    if not news_link:
                        continue
                        
                    source_url = news_link.get('href', '')
                    if not source_url:
                        continue
                        
                    # Extract title and date
                    h4_text = item.find('h4').text.strip()
                    date_str, title = h4_text.split(' - ', 1)
                    
                    # Parse date (assuming format MM/DD/YYYY)
                    try:
                        published_date = datetime.strptime(date_str, '%m/%d/%Y')
                    except ValueError:
                        logging.error(f"Could not parse date: {date_str}")
                        continue
                    
                    # Check if we already have this news item
                    if not IssuerNews.objects.filter(
                        issuer=issuer,
                        source_url=source_url
                    ).exists():
                        news = IssuerNews(
                            issuer=issuer,
                            title=title,
                            content='',  # We could fetch the content from seinet.com.mk if needed
                            published_date=published_date,
                            source_url=source_url
                        )
                        news.save()
                        logging.info(f"Added news for {issuer.code}: {title}")
                    
                except Exception as e:
                    logging.error(f"Error processing news item for {issuer.code}: {str(e)}")
                    continue
                    
        except requests.RequestException as e:
            logging.error(f"Request failed for {issuer.code}: {str(e)}")
            return 