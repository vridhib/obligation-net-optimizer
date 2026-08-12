import pytest
import tempfile
import pandas as pd
from datetime import timedelta
from decimal import Decimal
from streaming.obligation_store import ObligationStore
from streaming.stream_simulator import StreamSimulator, Snapshot


pytestmark = pytest.mark.django_db

# ------------- Fixtures -------------
@pytest.fixture
def run_simulation():
    """
    Factory fixture that runs the simulator and returns the 
    Snapshot object.
    """
    def _run(
        rows: list[dict],
        initial_balances: dict[str, Decimal] | None = None,
        window_duration: timedelta = timedelta(minutes=1),
        speed_factor: float = 0
    ):
        csv_path = make_csv(rows)
        store = ObligationStore()
        snapshot = Snapshot()
        if initial_balances is None:
            initial_balances = {
                "A": Decimal(1000),
                "B": Decimal(1000),
                "C": Decimal(1000)
            }
        sim = StreamSimulator(
            store, snapshot, initial_balances,
            window_duration=window_duration,
            speed_factor=speed_factor
        )
        sim.run(csv_path)
        return snapshot
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
         "timestamp": "2026-07-15 08:00:30"}
    ]
    final = run_simulation(rows).get_snapshot()
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
         "timestamp": "2026-07-15 08:01:30"}
    ]
    final = run_simulation(rows).get_snapshot()
    # Balances are cumulative across windows
    assert final['balances']['A'] == Decimal(900)   # started 1000, paid 100
    assert final['balances']['B'] == Decimal(1050)  # 1000 + 100 - 50
    assert final['balances']['C'] == Decimal(1050)  # 1000 + 50


def test_empty_csv(run_simulation):
    final = run_simulation([], initial_balances={}).get_snapshot()
    assert final['total_settled'] == Decimal(0)


def test_liquidity_shortfall(run_simulation):
    rows = [
        {"tx_id": "1", "payer": "A", "payee": "B", "amount": 200.0, "currency": "USD",
         "timestamp": "2026-07-15 08:00:00"}
    ]
    final = run_simulation(rows, initial_balances={"A": Decimal(50), "B": Decimal(0)}).get_snapshot()
    assert final['total_failed'] == Decimal(200)
    assert final['failure_rate'] == Decimal(1)


def test_window_advances_with_gap(run_simulation):
    rows = [
        {"tx_id": "1", "payer": "A", "payee": "B", "amount": 100.0, "currency": "USD",
         "timestamp": "2026-07-15 08:10:00"},
        {"tx_id": "2", "payer": "B", "payee": "C", "amount": 50.0, "currency": "USD",
         "timestamp": "2026-07-15 08:30:00"}
    ]
    final = run_simulation(rows).get_snapshot()
    assert final['total_settled'] > 0   # the last window settles something


def test_netting_reduced_volume_and_saves_liquidity(run_simulation):
    """
    A cycle within one window that goes through multilateral netting
    should reduce the total settled volume below gross volume, and
    record the savings.
    """
    # All three obligations in the same minute (08:00:xx) form a cycle
    rows = [
        {"tx_id": "1", "payer": "A", "payee": "B", "amount": 100.0, "currency": "USD",
         "timestamp": "2026-07-15 08:00:00"},
        {"tx_id": "2", "payer": "B", "payee": "C", "amount": 80.0, "currency": "USD",
         "timestamp": "2026-07-15 08:00:20"},
        {"tx_id": "3", "payer": "C", "payee": "A", "amount": 50.0, "currency": "USD",
         "timestamp": "2026-07-15 08:00:40"}
    ]
    snapshot = run_simulation(rows)
    final = snapshot.get_snapshot()

    # Netting should occur: gross = 100+80+50=230, net < 230
    assert final['liquidity_saved'] > 0
    assert final['total_settled'] < final['gross_volume']

    # Check window_history recorded the metrics
    assert len(snapshot.window_history) == 1
    window = snapshot.window_history[0]
    assert window['gross_volume'] == Decimal(230)
    assert window['liquidity_saved'] == window['gross_volume'] - window['total_settled']
    assert window['failure_rate'] == Decimal(0)


def test_multiple_windows_history_and_metrics(run_simulation):
    # Obligations spanning 3 1‑min windows: 08:00, 08:01, 08:02
    rows = [
        {"tx_id": "1", "payer": "A", "payee": "B", "amount": 100.0, "currency": "USD",
         "timestamp": "2026-07-15 08:00:00"},
        {"tx_id": "2", "payer": "B", "payee": "C", "amount": 50.0, "currency": "USD",
         "timestamp": "2026-07-15 08:00:30"},      # same window (08:00)
        {"tx_id": "3", "payer": "C", "payee": "A", "amount": 30.0, "currency": "USD",
         "timestamp": "2026-07-15 08:01:00"},      # next window (08:01)
        {"tx_id": "4", "payer": "A", "payee": "C", "amount": 10.0, "currency": "USD",
         "timestamp": "2026-07-15 08:02:15"}       # next window (08:02)
    ]
    snapshot = run_simulation(rows)
    assert len(snapshot.window_history) == 3

    # Check that windows are ordered and have reasonable metrics
    previous_end = None
    for window in snapshot.window_history:
        if previous_end is not None:
            assert window['last_window_end'] > previous_end
        previous_end = window['last_window_end']

        # gross_volume must be positive for windows that had obls
        assert window['gross_volume'] > 0
        # liquidity_saved is per-window (not cumulative)
        assert window['liquidity_saved'] >= 0
        # total_settled should be lt/e to gross_volume
        assert window['total_settled'] <= window['gross_volume']
        # failure_rate should be between 0 and 1
        assert 0 <= window['failure_rate'] <= 1

    assert snapshot.window_history[0]['gross_volume'] == Decimal(150)
    assert snapshot.window_history[0]['liquidity_used'] == Decimal(150)
    assert snapshot.window_history[1]['gross_volume'] == Decimal(30)
    assert snapshot.window_history[1]['liquidity_used'] == Decimal(180)
    assert snapshot.window_history[2]['gross_volume'] == Decimal(10)
    assert snapshot.window_history[2]['liquidity_used'] == Decimal(190)


def test_cumulative_liquidity_used(run_simulation):
    rows = [
        {"tx_id": "1", "payer": "A", "payee": "B", "amount": 100.0, "currency": "USD",
         "timestamp": "2026-07-15 08:00:00"},
        {"tx_id": "2", "payer": "B", "payee": "C", "amount": 50.0, "currency": "USD",
         "timestamp": "2026-07-15 08:01:00"}
    ]
    snapshot = run_simulation(rows)
    history = snapshot.window_history
    assert len(history) == 2
    assert history[0]['liquidity_used'] == Decimal(100)
    assert history[1]['liquidity_used'] == Decimal(150)
