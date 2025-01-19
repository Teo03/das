from django.urls import path
from . import commands

urlpatterns = [
    path('train-predictor/', commands.train_price_predictor, name='api-train-predictor'),
    path('fetch-stock-data/', commands.fetch_stock_data, name='api-fetch-stock-data'),
    path('fetch-all-stock-data/', commands.fetch_all_stock_data, name='api-fetch-all-stock-data'),
    path('get-symbols/', commands.get_symbols, name='api-get-symbols'),
    path('fetch-news/', commands.fetch_issuer_news, name='api-fetch-news'),
    path('fetch-news-content/', commands.fetch_news_content, name='api-fetch-news-content'),
    path('update-issuer-data/', commands.update_issuer_data, name='api-update-issuer-data'),
    path('clear-stock-prices/', commands.clear_stock_prices, name='api-clear-stock-prices'),
    path('import-csv-data/', commands.import_csv_stock_data, name='api-import-csv-data'),
] 