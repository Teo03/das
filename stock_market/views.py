from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def view_stocks(request):
    return render(request, 'view_stocks.html')

def predict(request):
    return render(request, 'predict.html')

def about(request):
    return render(request, 'about.html')
