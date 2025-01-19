from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.management import call_command
from datetime import datetime
import json

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_price_predictor(request):
    """Train price prediction models for all stocks or a specific symbol"""
    symbol = request.data.get('symbol')
    try:
        if symbol:
            call_command('train_price_predictor', symbol=symbol)
        else:
            call_command('train_price_predictor')
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetch_stock_data(request):
    """Fetch stock data for a specific symbol and date range"""
    symbol = request.data.get('symbol')
    from_date = request.data.get('from_date')
    to_date = request.data.get('to_date')
    
    if not all([symbol, from_date, to_date]):
        return Response(
            {'error': 'symbol, from_date, and to_date are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        call_command('fetch_stock_data_for_symbol', 
                    symbol=symbol,
                    from_date=from_date,
                    to_date=to_date,
                    return_data=True)
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetch_all_stock_data(request):
    """Fetch historical stock data for all symbols"""
    from_year = request.data.get('from_year', 2014)
    debug = request.data.get('debug', False)
    
    try:
        call_command('fetch_all_stock_data', 
                    from_year=from_year,
                    debug=debug)
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_symbols(request):
    """Get all available stock symbols"""
    try:
        call_command('get_all_symbols')
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetch_issuer_news(request):
    """Fetch latest news for issuers"""
    issuer = request.data.get('issuer')
    try:
        if issuer:
            call_command('fetch_issuer_news', issuer=issuer)
        else:
            call_command('fetch_issuer_news')
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetch_news_content(request):
    """Fetch content for news items"""
    empty_only = request.data.get('empty_only', False)
    try:
        call_command('fetch_issuer_news_content', empty_only=empty_only)
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_issuer_data(request):
    """Update issuer symbols and names"""
    try:
        call_command('update_issuer_symbols')
        call_command('update_issuer_names')
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_stock_prices(request):
    """Clear all stock price records"""
    try:
        call_command('clear_stock_prices')
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_csv_stock_data(request):
    """Import stock data from CSV files"""
    threads = request.data.get('threads')
    try:
        if threads:
            call_command('import_csv_stock_data', threads=threads)
        else:
            call_command('import_csv_stock_data')
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 