from django.core.management.base import BaseCommand
from core.pipeline import Pipeline, IssuerListFilter

class Command(BaseCommand):
    help = 'Gets all available stock symbols from MSE'

    def handle(self, *args, **options):
        pipeline = Pipeline()
        pipeline.add_filter(IssuerListFilter())
        
        symbols = pipeline.execute()

        from core.models import Issuer
        symbols_data = []
        for symbol in symbols:
            issuer = Issuer.objects.get(code=symbol)
            symbols_data.append({
                'symbol': issuer.code,
                'name': issuer.name
            })
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully extracted {len(symbols)} symbols'
            )
        )
        
        for symbol_data in symbols_data:
            self.stdout.write(f"{symbol_data['symbol']}: {symbol_data['name']}")
