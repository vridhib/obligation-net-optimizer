import factory
import uuid
from django.utils import timezone
from obligations.models import Obligation, NettingWindow


class ObligationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Obligation

    tx_id = factory.LazyFunction(uuid.uuid4)
    payer = factory.Sequence(lambda n: f"Bank_{n % 30}")
    payee = factory.Sequence(lambda n: f"Bank_{n % 30}")
    amount = 100.00
    currency = "USD"
    timestamp = factory.LazyFunction(timezone.now)
    status = Obligation.Status.PENDING


class NettingWindowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NettingWindow

    start_time = factory.LazyFunction(timezone.now)
    end_time = factory.LazyFunction(timezone.now)
    gross_obligation_count = 0
    net_obligation_count = 0
    net_volume = 0.0
    liquidity_saved = 0.0
    