from celery import shared_task
from .obligation_store import ObligationStore
from .stream_simulator import Snapshot, StreamSimulator
from datetime import timedelta
from decimal import Decimal


@shared_task
def run_simulation_task(csv_path, window_minutes=1, initial_balance=200_000):
    participants = [f"Bank_{i}" for i in range(30)]
    balances = {p: Decimal(initial_balance) for p in participants}

    store = ObligationStore()
    snapshot = Snapshot()
    sim = StreamSimulator(
        store, snapshot, balances,
        window_duration=timedelta(minutes=window_minutes),
        speed_factor=0
    )
    sim.run(csv_path)
    
    return {
        'windows_processed': len(snapshot.window_history),
        'total_settled': str(snapshot.total_settled),
        'liquidity_saved': str(snapshot.liquidity_saved)
    }
