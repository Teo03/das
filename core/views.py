from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from .models import Issuer, StockPrice
import json
from datetime import datetime
import numpy as np
import pandas as pd
from .technical_analysis import calculate_technical_indicators, generate_signals, get_consensus_signal

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
    
    # Convert to DataFrame for technical analysis
    df = pd.DataFrame(list(prices.values()))
    df = df.rename(columns={
        'last_trade_price': 'close_price',
        'max_price': 'high',
        'min_price': 'low'
    })
    
    # Calculate technical indicators for different periods
    periods = [1, 5, 20]  # 1 day, 1 week, 1 month
    indicators = calculate_technical_indicators(df, periods)
    
    # Generate signals for each period
    signals = {}
    consensus = {}
    for period in periods:
        signals[period] = generate_signals(indicators[period], period)
        consensus[period] = get_consensus_signal(signals[period], period)
    
    def handle_nan(value):
        if pd.isna(value) or np.isinf(value):
            return None
        if isinstance(value, float):
            return float(value)
        return value
    
    price_data = [
        {
            'date': price.date.strftime('%Y-%m-%d'),
            'close_price': float(price.last_trade_price),
            'volume': price.volume,
            'max_price': float(price.max_price),
            'min_price': float(price.min_price),
            'avg_price': float(price.avg_price),
            'price_change': float(price.price_change),
            'technical_indicators': {
                period: {
                    'moving_averages': {
                        'sma': handle_nan(indicators[period].iloc[i][f'sma_{period}']),
                        'ema': handle_nan(indicators[period].iloc[i][f'ema_{period}']),
                        'wma': handle_nan(indicators[period].iloc[i][f'wma_{period}']),
                        'tema': handle_nan(indicators[period].iloc[i][f'tema_{period}']),
                        'kama': handle_nan(indicators[period].iloc[i][f'kama_{period}'])
                    },
                    'oscillators': {
                        'rsi': handle_nan(indicators[period].iloc[i][f'rsi_{period}']),
                        'stoch': handle_nan(indicators[period].iloc[i][f'stoch_{period}']),
                        'cci': handle_nan(indicators[period].iloc[i][f'cci_{period}']),
                        'macd': handle_nan(indicators[period].iloc[i][f'macd_{period}']),
                        'willr': handle_nan(indicators[period].iloc[i][f'willr_{period}'])
                    },
                    'signals': {
                        'moving_averages': {
                            'sma': signals[period].iloc[i][f'sma_signal_{period}'],
                            'ema': signals[period].iloc[i][f'ema_signal_{period}'],
                            'wma': signals[period].iloc[i][f'wma_signal_{period}'],
                            'tema': signals[period].iloc[i][f'tema_signal_{period}'],
                            'kama': signals[period].iloc[i][f'kama_signal_{period}']
                        },
                        'oscillators': {
                            'rsi': signals[period].iloc[i][f'rsi_signal_{period}'],
                            'stoch': signals[period].iloc[i][f'stoch_signal_{period}'],
                            'cci': signals[period].iloc[i][f'cci_signal_{period}'],
                            'macd': signals[period].iloc[i][f'macd_signal_{period}'],
                            'willr': signals[period].iloc[i][f'willr_signal_{period}']
                        },
                        'consensus': consensus[period]
                    }
                }
                for period in periods
            }
        }
        for i, price in enumerate(prices)
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
        'last_price': last_price_data,
        'technical_analysis': {
            period: {
                'consensus': consensus[period]
            }
            for period in periods
        }
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