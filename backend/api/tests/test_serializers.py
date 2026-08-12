import uuid
from api.serializers import ObligationSerializer


def make_valid_data(**overrides):
    """Return a valid dictionary for ObligationSerializer."""
    data = {
        "tx_id": str(uuid.uuid4()),
        "payer": "Bank_A",
        "payee": "Bank_B",
        "amount": "150.00",
        "currency": "USD",
        "timestamp": "2026-08-11T08:00:00Z",
    }
    data.update(overrides)
    return data


def test_valid_data_is_valid():
    serializer = ObligationSerializer(data=make_valid_data())
    assert serializer.is_valid(), serializer.errors


def test_missing_required_field():
    data = make_valid_data()
    del data["amount"]
    serializer = ObligationSerializer(data=data)
    assert not serializer.is_valid()
    assert "amount" in serializer.errors


def test_missing_multiple_required_fields():
    data = {"payer": "A"}
    serializer = ObligationSerializer(data=data)
    assert not serializer.is_valid()
    assert "amount" in serializer.errors
    assert "payee" in serializer.errors


def test_invalid_amount_type():
    data = make_valid_data(amount="not-a-number")
    serializer = ObligationSerializer(data=data)
    assert not serializer.is_valid()
    assert "amount" in serializer.errors


def test_invalid_timestamp_format():
    data = make_valid_data(timestamp="2026/08/11 08:00")
    serializer = ObligationSerializer(data=data)
    assert not serializer.is_valid()
    assert "timestamp" in serializer.errors


def test_invalid_currency_choice():
    data = make_valid_data(currency="USD")           # valid
    assert ObligationSerializer(data=data).is_valid()
    data["currency"] = "US"                          # valid
    assert ObligationSerializer(data=data).is_valid()
    data["currency"] = "USDDDD"                      # too long
    assert not ObligationSerializer(data=data).is_valid()


def test_status_field_accepts_only_choices():
    data = make_valid_data()
    serializer = ObligationSerializer(data=data)
    if 'status' in serializer.fields:
        data['status'] = 'pending'
        assert ObligationSerializer(data=data).is_valid()
        data['status'] = 'invalid'
        assert not ObligationSerializer(data=data).is_valid()