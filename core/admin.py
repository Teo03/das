from django.contrib import admin
from .models import Issuer, StockPrice, IssuerNews

admin.site.register(Issuer)
admin.site.register(StockPrice)
admin.site.register(IssuerNews)