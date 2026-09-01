from decimal import Decimal
import pandas as pd
import pytest
from datetime import datetime, timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from api import services
from .factories import NettingWindowFactory, NetPositionFactory, SettlementAttemptFactory, ObligationFactory
from obligations.models import Obligation, NettingWindow


pytestmark = pytest.mark.django_db

# ---------- Tests for `normalize_obligations_df` ----------
def test_normalize_obligations_missing_columns():
    df = pd.DataFrame({"payer": ["A"], "payee": ["B"], "amount": [10.0]})
    with pytest.raises(ValueError, match="Missing required columns"):
        services.normalize_obligations_df(df)


def test_normalize_obligations_df_adds_defaults():
    df = pd.DataFrame({
        "payer": ["A"],
        "payee": ["B"],
        "amount": [10.0],
        "timestamp": ["2026-08-11T08:00:00Z"]
    })
    normalized = services.normalize_obligations_df(df)
    assert "tx_id" not in normalized.columns
    assert "currency" in normalized.columns
    assert "status" in normalized.columns
    assert normalized.loc[0, "currency"] == "USD"
    assert normalized.loc[0, "status"] == Obligation.Status.PENDING


def test_normalize_obligations_df_adds_time_to_dates():
    df = pd.DataFrame({
        "payer": ["A"],
        "payee": ["B"],
        "amount": [10.0],
        "timestamp": ["2026-08-11"]
    })
    normalized = services.normalize_obligations_df(df)
    # Should have a timestamp
    assert normalized["timestamp"].dt.tz is not None


def test_normalize_obligations_df_converts_datetime_to_utc():
    df = pd.DataFrame({
        "payer": ["A"],
        "payee": ["B"],
        "amount": [10.0],
        "timestamp": ["2026-08-11T10:00:00+02:00"]
    })
    normalized = services.normalize_obligations_df(df)
    ts = normalized.loc[0, "timestamp"]
    assert ts.tzinfo is not None
    # Should be converted to UTC (10:00 +02:00 = 8:00 UTC)
    assert ts == pd.Timestamp("2026-08-11T8:00:00+0:00")
        

# ------- Tests for `create_obligations_from_records` ------
def test_create_obligations_from_records_valid():
    result = services.create_obligations_from_records([
        {
            "payer": "A",
            "payee": "B",
            "amount": "100.00",
            "currency": "USD",
            "timestamp": "2026-08-11T08:00:00Z"
        }
    ])
    assert result["created_count"] == 1
    assert result["errors_count"] == 0


def test_create_obligations_from_records_invalid():
    result = services.create_obligations_from_records([
        {"payer": "A", "payee": "B"}  # missing amount, timestamp
    ])
    assert result["created_count"] == 0
    assert result["errors_count"] == 1
    assert "amount" in result["errors"][0]


# --------- Tests for `create_obligations_from_csv` --------
def test_create_obligations_from_csv_valid():
    csv_content = (
        "payer,payee,amount,timestamp\n"
        "A,B,100.00,2026-08-11T08:00:00Z\n"
        "C,D,50.00,2026-08-11T08:01:00Z\n"
    )
    csv_file = SimpleUploadedFile("test.csv", csv_content.encode(), content_type="text/csv")
    result = services.create_obligations_from_csv(csv_file)
    assert result["created_count"] == 2
    assert Obligation.objects.count() == 2


def test_create_obligations_from_csv_invalid_file():
    empty_file = SimpleUploadedFile("empty.csv", b"", content_type="text/csv")
    with pytest.raises(ValueError, match="Failed to parse CSV"):
        services.create_obligations_from_csv(empty_file)


# ---------- Tests for `get_net_positions_for_window` ----------
def test_get_net_positions_for_window_latest():
    window = NettingWindowFactory()
    NetPositionFactory(window=window, participant="Bank_A", net_amount=Decimal("-100.00"))
    result = services.get_net_positions_for_window("latest")
    assert result["window_id"] == window.window_id
    assert len(result["positions"]) == 1
    assert result["positions"][0]["participant"] == "Bank_A"


def test_get_net_positions_for_window_by_id():
    window = NettingWindowFactory()
    result = services.get_net_positions_for_window(str(window.window_id))
    assert result["window_id"] == window.window_id


def test_get_net_positions_for_window_invalid_id():
    result = services.get_net_positions_for_window("abc")
    assert result is None


def test_get_net_positions_for_window_no_windows():
    result = services.get_net_positions_for_window("latest")
    assert result == {"window_id": None, "positions": []}


# ---------- Tests for `get_netting_summary` ----------
def test_get_netting_summary_aggregates_correctly():
    w1 = NettingWindowFactory(
        gross_obligation_count=2,
        net_obligation_count=1,
        gross_volume=Decimal("230.00"),
        net_volume=Decimal("180.00"),
        liquidity_saved=Decimal("50.00"),
    )
    w2 = NettingWindowFactory(
        gross_obligation_count=1,
        net_obligation_count=1,
        gross_volume=Decimal("30.00"),
        net_volume=Decimal("30.00"),
        liquidity_saved=Decimal("0.00"),
    )
    SettlementAttemptFactory(window=w1, amount=Decimal("180.00"), status="settled")
    SettlementAttemptFactory(window=w2, amount=Decimal("30.00"), status="failed")

    summary = services.get_netting_summary()
    assert summary["total_windows"] == 2
    assert summary["gross_obligation_count"] == 3
    assert summary["net_obligation_count"] == 2
    assert summary["gross_volume"] == "260.00"
    assert summary["net_volume"] == "210.00"
    assert summary["liquidity_saved"] == "50.00"
    assert summary["settled_attempts"] == 1
    assert summary["failed_attempts"] == 1


def test_get_netting_summary_no_windows():
    summary = services.get_netting_summary()
    assert summary["total_windows"] == 0
    assert summary["gross_volume"] == "0"


# --------- Tests for `get_graph_for_window` ----------
def test_get_graph_for_window_gross():
    window = NettingWindowFactory()
    ObligationFactory(
        payer="Bank_A", payee="Bank_B", amount=Decimal("100.00"),
        timestamp=datetime.now(timezone.utc), netting_window=window, status=Obligation.Status.NETTED
    )
    ObligationFactory(
        payer="Bank_A", payee="Bank_B", amount=Decimal("50.00"),
        timestamp=datetime.now(timezone.utc), netting_window=window, status=Obligation.Status.NETTED
    )
    ObligationFactory(
        payer="Bank_B", payee="Bank_C", amount=Decimal("75.00"),
        timestamp=datetime.now(timezone.utc), netting_window=window, status=Obligation.Status.NETTED
    )

    result = services.get_graph_for_window(window.window_id, "gross")
    assert result["window_id"] == window.window_id
    assert result["view"] == "gross"
    assert len(result["nodes"]) == 3   # A, B, C
    # Edges aggregated: A->B = 150, B->C = 75
    assert len(result["edges"]) == 2
    print(result["edges"])
    assert any(e["source"] == "Bank_A" and e["target"] == "Bank_B" and e["amount"] == "150" for e in result["edges"])


def test_get_graph_for_window_net():
    window = NettingWindowFactory()
    NetPositionFactory(window=window, participant="Bank_A", net_amount=Decimal("-100.00"))
    NetPositionFactory(window=window, participant="Bank_B", net_amount=Decimal("100.00"))
    SettlementAttemptFactory(window=window, payer="Bank_A", payee="Bank_B", amount=Decimal("100.00"), status="settled")

    result = services.get_graph_for_window(window.window_id, "net")
    assert result["view"] == "net"
    assert len(result["nodes"]) == 2
    assert result["nodes"][0]["net_amount"] in ("-100.00", "100.00")
    assert len(result["edges"]) == 1
    assert result["edges"][0]["source"] == "Bank_A"
    assert result["edges"][0]["target"] == "Bank_B"
    assert result["edges"][0]["amount"] == "100.00"


def test_get_graph_for_window_invalid_view():
    window = NettingWindowFactory()
    with pytest.raises(ValueError):
        services.get_graph_for_window(window.window_id, "invalid")


def test_get_graph_for_window_nonexistent():
    with pytest.raises(NettingWindow.DoesNotExist):
        services.get_graph_for_window(99999, "net")