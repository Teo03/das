from django.db import models

class Issuer(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class IssuerNews(models.Model):
    issuer = models.ForeignKey(Issuer, on_delete=models.CASCADE, related_name='news')
    title = models.CharField(max_length=500)
    content = models.TextField()
    published_date = models.DateTimeField()
    source_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Issuer News'
        ordering = ['-published_date']
        indexes = [
            models.Index(fields=['published_date']),
            models.Index(fields=['issuer', 'published_date'])
        ]

    def __str__(self):
        return f"{self.issuer.code} - {self.title[:50]}"

class StockPrice(models.Model):
    issuer = models.ForeignKey(Issuer, on_delete=models.CASCADE)
    date = models.DateField()
    last_trade_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_change = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.IntegerField()
    turnover_best = models.DecimalField(max_digits=15, decimal_places=2)
    total_turnover = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        unique_together = ['issuer', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['issuer', 'date'])
        ]