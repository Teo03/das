from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('api/fetch-data/', views.fetch_data, name='fetch_data'),
    path('api/stock-data/<str:symbol>/', views.stock_data, name='stock_data'),
] 