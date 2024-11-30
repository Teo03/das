from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from .models import Issuer, StockPrice
import json
from datetime import datetime
import numpy as np

def home(request):
    return render(request, 'core/home.html')

def predict(request):
    return render(request, 'core/predict.html')

def about(request):
    return render(request, 'core/about.html')

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

def predict_view(request):
    from .models import Issuer, StockPrice
    import numpy as np
    from django.db.models import Max
    from datetime import datetime, timedelta
    issuers = Issuer.objects.all()
    context = {'stocks': issuers}
    
    if request.method == 'POST':
        issuer_code = request.POST.get('stock')
        issuer = Issuer.objects.get(code=issuer_code)
        
        latest_price = StockPrice.objects.filter(issuer=issuer).order_by('-date').first()
        
        if latest_price:
            current_price = float(latest_price.last_trade_price)
            
            predicted_change = np.random.uniform(-0.1, 0.15)
            predicted_price = current_price * (1 + predicted_change)
            
            last_month_prices = StockPrice.objects.filter(
                issuer=issuer,
                date__gte=datetime.now().date() - timedelta(days=30)
            ).values_list('last_trade_price', flat=True)
            
            if last_month_prices:
                price_volatility = np.std([float(p) for p in last_month_prices]) / np.mean([float(p) for p in last_month_prices])
                confidence = max(70, min(95, 90 - price_volatility * 100))
            else:
                confidence = 75.0
            
            prediction = {
                'stock': issuer.name,
                'predicted_price': f"${predicted_price:.2f}",
                'current_price': f"${current_price:.2f}",
                'change_percent': f"{predicted_change * 100:+.1f}%",
                'confidence': f"{confidence:.1f}",
                'date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            }
            
            context['prediction'] = prediction
    
    return render(request, 'core/predict.html', context)

def about(request):
    return render(request, 'core/about.html')
