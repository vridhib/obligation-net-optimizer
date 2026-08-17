import uuid
from decimal import Decimal
from ..serializers import ObligationSerializer, NettingWindowSerializer, ParticipantBalanceSerializer
import pytest
from .factories import NettingWindowFactory, NetPositionFactory, SettlementAttemptFactory, ParticipantBalanceFactory


def make_valid_obl_data(**overrides):
    """Return a valid dictionary for ObligationSerializer."""
    data = {
        "payer": "Bank_A",
        "payee": "Bank_B",
        "amount": "150.00",
        "currency": "USD",
        "timestamp": "2026-08-11T08:00:00Z",
    }
    data.update(overrides)
    return data


# ---------- ObligationSerializer ----------
def test_obligation_serializer_valid():
    serializer = ObligationSerializer(data=make_valid_obl_data())
    assert serializer.is_valid(), serializer.errors


def test_obligation_serializer_tx_id_is_read_only():
    data = make_valid_obl_data(tx_id=str(uuid.uuid4))
    serializer = ObligationSerializer(data=data)
    assert serializer.is_valid()
    assert "tx_id" not in serializer.validated_data


@pytest.mark.parametrize("field", ["payer", "payee", "amount", "timestamp"])
def test_obligation_serializer_missing_required_field(field):
    data = make_valid_obl_data()
    del data[field]
    serializer = ObligationSerializer(data=data)
    assert not serializer.is_valid()
    assert field in serializer.errors


def test_invalid_amount_type():
    data = make_valid_obl_data(amount="not-a-number")
    serializer = ObligationSerializer(data=data)
    assert not serializer.is_valid()
    assert "amount" in serializer.errors


def test_invalid_timestamp_format():
    data = make_valid_obl_data(timestamp="2026/08/11 08:00")
    serializer = ObligationSerializer(data=data)
    assert not serializer.is_valid()
    assert "timestamp" in serializer.errors


def test_invalid_currency_choice():
    data = make_valid_obl_data(currency="USD")           # valid
    assert ObligationSerializer(data=data).is_valid()
    data["currency"] = "US"                          # valid
    assert ObligationSerializer(data=data).is_valid()
    data["currency"] = "USDDDD"                      # too long
    assert not ObligationSerializer(data=data).is_valid()


def test_status_field_accepts_only_choices():
    data = make_valid_obl_data()
    serializer = ObligationSerializer(data=data)
    if 'status' in serializer.fields:
        data['status'] = 'pending'
        assert ObligationSerializer(data=data).is_valid()
        data['status'] = 'invalid'
        assert not ObligationSerializer(data=data).is_valid()


# ---------- NettingWindowSerializer ----------
@pytest.mark.django_db
def test_netting_window_serializer_includes_nested_data():
    window = NettingWindowFactory()
    NetPositionFactory(window=window, participant="Bank_A", net_amount=Decimal("-100.00"))
    NetPositionFactory(window=window, participant="Bank_B", net_amount=Decimal("100.00"))
    SettlementAttemptFactory(window=window, payer="Bank_A", payee="Bank_B", amount=Decimal("100.00"))

    serializer = NettingWindowSerializer(window)
    data = serializer.data

    assert len(data["net_positions"]) == 2
    assert data["net_positions"][0]["participant"] == "Bank_A"
    assert len(data["settlement_attempts"]) == 1
    assert data["settlement_attempts"][0]["status"] == "settled"


# ---------- ParticipantBalanceSerializer ----------
@pytest.mark.django_db
def test_participant_balance_serializer():
    balance = ParticipantBalanceFactory(participant="Bank_A", balance=Decimal("250.00"))
    serializer = ParticipantBalanceSerializer(balance)
    assert serializer.data["participant"] == "Bank_A"
    assert serializer.data["balance"] == "250.00"