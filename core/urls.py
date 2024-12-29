from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('stocks/', views.index, name='index'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('api/stock-data/<str:symbol>/', views.stock_data, name='stock_data'),
    path('predict/', views.predict_view, name='predict'),
    path('about/', views.about, name='about'),
    path('recommendations/', views.recommendations, name='recommendations'),
] 