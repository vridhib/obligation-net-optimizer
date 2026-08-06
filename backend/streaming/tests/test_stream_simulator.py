import pytest
import tempfile
import pandas as pd
from datetime import timedelta
from decimal import Decimal
from streaming.obligation_store import ObligationStore
from streaming.stream_simulator import StreamSimulator, Snapshot


# ------------- Fixtures -------------
@pytest.fixture
def run_simulation():
    """
    Factory fixture: returns a function that runs the simulator with
    custom rows and optional overrides, then returns the final snapshot.
    """
    def _run(
        rows: list[dict],
        initial_balances: dict[str, Decimal] | None = None,
        window_duration: timedelta = timedelta(minutes=1),
        speed_factor: float = 0,
    ):
        csv_path = make_csv(rows)
        store = ObligationStore()
        snapshot = Snapshot()
        if initial_balances is None:
            initial_balances = {
                "A": Decimal(1000),
                "B": Decimal(1000),
                "C": Decimal(1000),
            }
        sim = StreamSimulator(
            store, snapshot, initial_balances,
            window_duration=window_duration,
            speed_factor=speed_factor,
        )
        sim.run(csv_path)
        return snapshot.get_snapshot()
    return _run


# ------------- Helpers --------------
def make_csv(rows: list[dict]) -> str:
    """Write rows to a temporary CSV and return its path."""
    df = pd.DataFrame(rows)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        return f.name

    
# -------------- Tests ---------------
def test_single_window_basic_flow(run_simulation):
    rows = [
        {"tx_id": "1", "payer": "A", "payee": "B", "amount": 100.0, "currency": "USD",
         "timestamp": "2026-07-15 08:00:00"},
        {"tx_id": "2", "payer": "B", "payee": "C", "amount": 50.0, "currency": "USD",
         "timestamp": "2026-07-15 08:00:30"},
    ]
    final = run_simulation(rows)
    assert final['total_settled'] == Decimal(150)
    assert final['total_failed'] == Decimal(0)
    assert final['net_positions']['A'] == Decimal(-100)
    assert final['net_positions']['B'] == Decimal(50)
    assert final['net_positions']['C'] == Decimal(50)


def test_multiple_windows(run_simulation):
    rows = [
        {"tx_id": "1", "payer": "A", "payee": "B", "amount": 100.0, "currency": "USD",
         "timestamp": "2026-07-15 08:00:00"},
        {"tx_id": "2", "payer": "B", "payee": "C", "amount": 50.0, "currency": "USD",
         "timestamp": "2026-07-15 08:01:30"},
    ]
    final = run_simulation(rows)
    # Balances are cumulative across windows
    assert final['balances']['A'] == Decimal(900)   # started 1000, paid 100
    assert final['balances']['B'] == Decimal(1050)  # 1000 + 100 - 50
    assert final['balances']['C'] == Decimal(1050)  # 1000 + 50


def test_empty_csv(run_simulation):
    final = run_simulation([], initial_balances={})
    assert final['total_settled'] == Decimal(0)


def test_liquidity_shortfall(run_simulation):
    rows = [
        {"tx_id": "1", "payer": "A", "payee": "B", "amount": 200.0, "currency": "USD",
         "timestamp": "2026-07-15 08:00:00"},
    ]
    final = run_simulation(rows, initial_balances={"A": Decimal(50), "B": Decimal(0)})
    assert final['total_failed'] == Decimal(200)
    assert final['failure_rate'] == Decimal(1)


def test_window_advances_with_gap(run_simulation):
    rows = [
        {"tx_id": "1", "payer": "A", "payee": "B", "amount": 100.0, "currency": "USD",
         "timestamp": "2026-07-15 08:10:00"},
        {"tx_id": "2", "payer": "B", "payee": "C", "amount": 50.0, "currency": "USD",
         "timestamp": "2026-07-15 08:30:00"},
    ]
    final = run_simulation(rows)
    assert final['total_settled'] > 0   # the last window settles something