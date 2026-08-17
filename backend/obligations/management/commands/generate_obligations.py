from django.core.management.base import BaseCommand
from ...models import Obligation
from ...data_generator.generate_obligations import generate_obligations

class Command(BaseCommand):
    help = "Generate synthetic obligations"

    def add_arguments(self, parser):
        parser.add_argument('--cycles', type=int, default=50)
        parser.add_argument('--noise', type=int, default=3)
        parser.add_argument('--output', type=str, help='Export to CSV instead of DB')

    def handle(self, *args, **options):
        # Generate obligations
        df = generate_obligations(options['cycles'], options['noise'])

        # If set to CSV option, output file
        if options['output']:
            df.to_csv(options['output'], index=False)
            self.stdout.write(f"CSV saved to {options['output']}")
        # Otherwise, bulk create Obligation objects
        else:
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
            self.stdout.write(f"Loaded {len(obligations)} obligations.")