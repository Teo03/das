from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.management import call_command
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Issuer, StockPrice
from datetime import datetime, timedelta
import json

@ensure_csrf_cookie
def index(request):
    issuers = Issuer.objects.all().order_by('code')
    return render(request, 'core/index.html', {'issuers': issuers})

@ensure_csrf_cookie
def stock_detail(request, symbol):
    issuer = get_object_or_404(Issuer, code=symbol)
    prices = StockPrice.objects.filter(issuer=issuer).order_by('-date')[:30]  # Last 30 days
    
    price_data = [
        {
            'date': price.date.strftime('%Y-%m-%d'),
            'close_price': float(price.last_trade_price),
            'volume': price.volume
        }
        for price in prices
    ]
    
    return render(request, 'core/stock_detail.html', {
        'issuer': issuer,
        'prices': json.dumps(price_data),
        'last_price': prices.first()
    })

def fetch_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            if data.get('command') == 'get_all_symbols':
                call_command('get_all_symbols')
            else:
                symbol = data.get('symbol')
                from_date = data.get('from_date')
                to_date = data.get('to_date')
                
                call_command('fetch_stock_data_for_symbol', 
                            symbol=symbol,
                            from_date=from_date,
                            to_date=to_date)
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
