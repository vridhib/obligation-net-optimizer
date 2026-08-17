import factory
from factory import fuzzy
import uuid
from datetime import timedelta
from django.utils import timezone
from obligations.models import Obligation, NettingWindow, NetPosition, SettlementAttempt, ParticipantBalance


class ObligationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Obligation

    tx_id = factory.LazyFunction(uuid.uuid4)
    payer = factory.Sequence(lambda n: f"Bank_{n % 30}")
    payee = factory.Sequence(lambda n: f"Bank_{(n + 1) % 30}")
    amount = fuzzy.FuzzyDecimal(50.00, 100.00, 2)
    currency = "USD"
    timestamp = factory.LazyFunction(timezone.now)
    status = Obligation.Status.PENDING


class NettingWindowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NettingWindow

    start_time = factory.LazyFunction(
        lambda: timezone.now() - timedelta(minutes=1)
    )
    end_time = factory.LazyFunction(timezone.now)
    gross_obligation_count = 0
    net_obligation_count = 0
    gross_volume = 0.00
    net_volume = 0.00
    liquidity_saved = 0.00


class NetPositionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NetPosition

    window = factory.SubFactory(NettingWindowFactory)
    participant = factory.Sequence(lambda n: f"Bank_{n % 30}")
    net_amount = fuzzy.FuzzyDecimal(0.00, 1000.00, 2)


class SettlementAttemptFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SettlementAttempt

    window = factory.SubFactory(NettingWindowFactory)
    payer = factory.Sequence(lambda n: f"Bank_{n % 30}")
    payee = factory.Sequence(lambda n: f"Bank_{(n + 1) % 30}")
    amount = fuzzy.FuzzyDecimal(0.00, 1000.00, 2)
    status = SettlementAttempt.Status.SETTLED
    attempt_number = 1


class ParticipantBalanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ParticipantBalance

    participant = factory.Sequence(lambda n: f"Bank_{n % 30}")
    balance = fuzzy.FuzzyDecimal(0.00, 1000.00, 2)