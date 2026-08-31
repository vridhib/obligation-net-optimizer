from celery import shared_task
from datetime import timedelta
from decimal import Decimal
from obligations.models import Obligation
from .obligation_store import ObligationStore, Obligation as ObligationData
from .stream_simulator import Snapshot, StreamSimulator


@shared_task
def run_simulation_task(window_minutes=1, initial_balance=200_000):
    pending = Obligation.objects.filter(status=Obligation.Status.PENDING).order_by("timestamp")

    if not pending.exists():
        return {
        'windows_processed': 0,
        'total_settled': 0,
        'liquidity_saved': 0 
        }

    obligations = [
        ObligationData(
            tx_id=str(o.tx_id),
            payer=o.payer,
            payee=o.payee,
            timestamp=o.timestamp,
            amount=o.amount
        )
        for o in pending
    ]

    participants = {o.payer for o in obligations} | {o.payee for o in obligations}
    balances = {p: Decimal(initial_balance) for p in participants}

    store = ObligationStore()
    snapshot = Snapshot()
    sim = StreamSimulator(
        store, snapshot, balances,
        window_duration=timedelta(minutes=window_minutes),
        speed_factor=0
    )
    sim.run(obligations)
    
    return {
        'windows_processed': len(snapshot.window_history),
        'total_settled': str(snapshot.total_settled),
        'liquidity_saved': str(snapshot.liquidity_saved)
    }
