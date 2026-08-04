from decimal import Decimal
from ..settlement import settlement_scheduler


def test_settlement_all_funds_sufficient():
    payments = [("A", "B", Decimal(100)), ("B", "C", Decimal(50))]
    balances = {"A": Decimal(200), "B": Decimal(0), "C": Decimal(0)}
    result = settlement_scheduler(payments, balances)
    assert result["failed"] == []
    assert result["final_balances"]["A"] == Decimal(100)
    assert result["final_balances"]["B"] == Decimal(50)
    assert result["final_balances"]["C"] == Decimal(50)


def test_settlement_insufficient_funds():
    payments = [("A", "B", Decimal(100))]
    balances = {"A": Decimal(50), "B": Decimal(0)}
    result = settlement_scheduler(payments, balances)
    assert len(result["failed"]) == 1
    assert result["total_failed"] == Decimal(100)
    assert result["failure_rate"] == Decimal(1)


def test_settlement_second_pass_clears_after_receive():
    # A -> B -> C -> A
    # 0 -> 100 -> 100 -> 100
    payments = [("A", "B", Decimal(100)), ("B", "C", Decimal(100)), ("C", "A", Decimal(100))]
    balances = {"A": Decimal(0), "B": Decimal(100), "C": Decimal(100)}
    result = settlement_scheduler(payments, balances)
    assert result["failed"] == []
    assert result["final_balances"]["A"] == Decimal(0)
    assert result["final_balances"]["B"] == Decimal(100)


def test_settlement_empty():
    result = settlement_scheduler([], {"A": Decimal(100)})
    assert result['total_settled'] == Decimal(0)
    assert result['settled'] == [] and result['failed'] == []