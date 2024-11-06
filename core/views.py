from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.management import call_command
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from .models import Issuer, StockPrice
import json

@ensure_csrf_cookie
def index(request):
    issuers = Issuer.objects.all().order_by('code')
    return render(request, 'core/index.html', {'issuers': issuers})

@ensure_csrf_cookie
def stock_detail(request, symbol):
    issuer = get_object_or_404(Issuer, code=symbol)
    prices = StockPrice.objects.filter(issuer=issuer).order_by('-date')
    
    price_data = [
        {
            'date': price.date.strftime('%Y-%m-%d'),
            'close_price': float(price.last_trade_price),
            'volume': price.volume,
            'max_price': float(price.max_price),
            'min_price': float(price.min_price),
            'avg_price': float(price.avg_price),
            'price_change': float(price.price_change)
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
            elif data.get('command') == 'fetch_stock_data':
                symbol = data.get('symbol')
                from_date = data.get('from_date')
                to_date = data.get('to_date')
                
                call_command('fetch_stock_data_for_symbol', 
                           symbol=symbol,
                           from_date=from_date,
                           to_date=to_date,
                           quiet=True)
                
                # Update the issuer's last_updated timestamp with timezone aware datetime
                issuer = Issuer.objects.get(code=symbol)
                issuer.last_updated = timezone.now()
                issuer.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def stock_data(request, symbol):
    issuer = get_object_or_404(Issuer, code=symbol)
    prices = StockPrice.objects.filter(issuer=issuer).order_by('-date')
    
    price_data = [
        {
            'date': price.date.strftime('%Y-%m-%d'),
            'close_price': float(price.last_trade_price),
            'volume': price.volume,
            'max_price': float(price.max_price),
            'min_price': float(price.min_price),
            'avg_price': float(price.avg_price),
            'price_change': float(price.price_change)
        }
        for price in prices
    ]
    
    last_price = prices.first()
    last_price_data = None
    if last_price:
        last_price_data = {
            'date': last_price.date.strftime('%Y-%m-%d'),
            'last_trade_price': str(last_price.last_trade_price),
            'max_price': str(last_price.max_price),
            'min_price': str(last_price.min_price),
            'avg_price': str(last_price.avg_price),
            'price_change': str(last_price.price_change),
            'volume': last_price.volume,
            'total_turnover': str(last_price.total_turnover)
        }
    
    return JsonResponse({
        'prices': price_data,
        'last_price': last_price_data
    })
