from decimal import Decimal
from ..settlement import settlement_scheduler
from datetime import datetime, timezone


def test_settlement_all_funds_sufficient():
    ts = datetime(2026, 7, 15, 8, 0, 0, 0, tzinfo=timezone.utc)
    payments = [
        ("A", "B", Decimal(100), ts), 
        ("B", "C", Decimal(50), ts)
    ]
    balances = {"A": Decimal(200), "B": Decimal(0), "C": Decimal(0)}
    result = settlement_scheduler(payments, balances)
    assert result["failed"] == []
    assert result["final_balances"]["A"] == Decimal(100)
    assert result["final_balances"]["B"] == Decimal(50)
    assert result["final_balances"]["C"] == Decimal(50)


def test_settlement_insufficient_funds():
    payments = [("A", "B", Decimal(100), datetime(2026, 7, 15, 8, 0, 0, tzinfo=timezone.utc))]
    balances = {"A": Decimal(50), "B": Decimal(0)}
    result = settlement_scheduler(payments, balances)
    assert len(result["failed"]) == 1
    assert result["total_failed"] == Decimal(100)
    assert result["failure_rate"] == Decimal(1)


def test_settlement_second_pass_clears_after_receive():
    # A -> B -> C -> A
    # 0 -> 100 -> 100 -> 100
    ts = datetime(2026, 7, 15, 8, 0, 0, tzinfo=timezone.utc)
    payments = [
        ("A", "B", Decimal(100), ts), 
        ("B", "C", Decimal(100), ts), 
        ("C", "A", Decimal(100), ts)
    ]
    balances = {"A": Decimal(0), "B": Decimal(100), "C": Decimal(100)}
    result = settlement_scheduler(payments, balances)
    assert result["failed"] == []
    assert result["final_balances"]["A"] == Decimal(0)
    assert result["final_balances"]["B"] == Decimal(100)
    assert result["final_balances"]["C"] == Decimal(100)


def test_settlement_timestamp_amount_priority():
    ts_1 = datetime(2026, 7, 15, 8, 0, 30, tzinfo=timezone.utc)
    ts_2 = datetime(2026, 7, 15, 8, 0, 30, tzinfo=timezone.utc)
    ts_3 = datetime(2026, 7, 15, 8, 0, 0, tzinfo=timezone.utc)
    payments = [
        ("A", "B", Decimal(100), ts_1), # P1
        ("B", "C", Decimal(50), ts_2),  # P2
        ("C", "A", Decimal(100), ts_3)  # P3
    ]
    balances = {"A": Decimal(200), "B": Decimal(100), "C": Decimal(100)}
    result = settlement_scheduler(payments, balances)
    # P3 (earliest ts), P1 (same ts as P3 but higher amt), P2
    assert result["settled"][0] == ("C", "A", Decimal(100))
    assert result["settled"][1] == ("A", "B", Decimal(100))
    assert result["settled"][2] == ("B", "C", Decimal(50))
    assert result["final_balances"]["A"] == Decimal(200)
    assert result["final_balances"]["B"] == Decimal(150)
    assert result["final_balances"]["C"] == Decimal(50)


def test_settlement_empty():
    result = settlement_scheduler([], {"A": Decimal(100)})
    assert result['total_settled'] == Decimal(0)
    assert result['settled'] == [] and result['failed'] == []