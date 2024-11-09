from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from .models import Issuer, StockPrice
import json
from datetime import datetime

@ensure_csrf_cookie
def index(request):
    issuers = Issuer.objects.all().order_by('code')
    return render(request, 'core/index.html', {'issuers': issuers})

@ensure_csrf_cookie
def stock_detail(request, symbol):
    issuer = get_object_or_404(Issuer, code=symbol)
    current_year = timezone.now().year
    start_date = datetime(current_year, 1, 1).date()
    end_date = timezone.now().date()
    
    prices = StockPrice.objects.filter(
        issuer=issuer,
        date__range=[start_date, end_date]
    ).order_by('-date')
    
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

def stock_data(request, symbol):
    issuer = get_object_or_404(Issuer, code=symbol)
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    prices_query = StockPrice.objects.filter(issuer=issuer)
    
    if from_date and to_date:
        prices_query = prices_query.filter(
            date__range=[from_date, to_date]
        ).order_by('-date')
    else:
        current_year = timezone.now().year
        start_date = datetime(current_year, 1, 1).date()
        end_date = timezone.now().date()
        prices_query = prices_query.filter(
            date__range=[start_date, end_date]
        ).order_by('-date')
    
    prices = prices_query.order_by('-date')
    
    if not prices.exists():
        return JsonResponse({
            'prices': [],
            'last_price': None,
            'message': 'No data available for the selected period'
        })
    
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
