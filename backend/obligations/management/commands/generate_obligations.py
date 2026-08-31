from django.core.management.base import BaseCommand
from ...models import Obligation
from ...data_generator.generate_obligations import generate_obligations

class Command(BaseCommand):
    help = "Generate synthetic obligations in the database"

    def add_arguments(self, parser):
        parser.add_argument('--cycles', type=int, default=50)
        parser.add_argument('--noise', type=int, default=3)

    def handle(self, *args, **options):
        # Generate obligations
        df = generate_obligations(options['cycles'], options['noise'])

        # Save to DB
        obligations = [
            Obligation(
                payer=row.payer,
                payee=row.payee,
                amount=row.amount,
                currency=row.currency,
                timestamp=row.timestamp,
                status='pending'
            ) for row in df.itertuples()
        ]
        Obligation.objects.bulk_create(obligations)
        self.stdout.write(f"Created {len(obligations)} obligations.")