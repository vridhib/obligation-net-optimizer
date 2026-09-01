import time
import logging
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from decimal import Decimal
from .obligation_store import ObligationStore, Obligation
from obligations.utils import persist_window
from netting.bilateral import bilateral_net
from netting.scc import multilateral_net
from netting.settlement import settlement_scheduler


logger = logging.getLogger(__name__)


class Snapshot:
    """
    Thread-safe holder for the latest engine state. Fields updated after 
    each netting window.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.net_positions = {}
        self.balances = {}
        self.total_settled = Decimal(0)
        self.total_failed = Decimal(0)
        self.liquidity_used = Decimal(0)
        self.liquidity_saved = Decimal(0)
        self.gross_volume = Decimal(0)
        self.failure_rate = Decimal(0)
        self.last_window_end = None
        self.window_history = []

    def update(self, **kwargs):
        with self._lock:
            for key, value in kwargs.items():
                setattr(self, key, value)
            # Record window history
            self.window_history.append({
                'last_window_end': self.last_window_end,
                'total_settled': self.total_settled,
                'total_failed': self.total_failed,
                'liquidity_used': self.liquidity_used,
                'liquidity_saved': self.liquidity_saved,
                'gross_volume': self.gross_volume,
                'failure_rate': self.failure_rate,
                'balances': dict(self.balances),
                'net_positions': dict(self.net_positions)
            })

    def get_snapshot(self) -> dict:
        with self._lock:
            return {
                'net_positions': dict(self.net_positions),
                'balances': dict(self.balances),
                'total_settled': self.total_settled,
                'total_failed': self.total_failed,
                'liquidity_used': self.liquidity_used,
                'liquidity_saved': self.liquidity_saved,
                'gross_volume': self.gross_volume,
                'failure_rate': self.failure_rate,
                'last_window_end': self.last_window_end
            }



class StreamSimulator:
    """
    Simulates a live obligation stream from a CSV file. Reads all obligations 
    and sorts them by timestamp (real data is already sorted). Advances a 
    simulated clock, inserting obligations into the store as time progresses. 
    At the end of each window (configurable duration), runs netting + settlement. 
    Records results in the Snapshot object. Can run in a background thread or 
    block the main thread.
    """

    def __init__(
        self,
        store: ObligationStore,
        snapshot: Snapshot,
        initial_balances: dict[str, Decimal],
        window_duration: timedelta = timedelta(minutes=1),
        speed_factor: float = 1.0 # >1 to speed up simulation, 0 for constant
    ):
        self.store = store
        self.snapshot = snapshot
        self.initial_balances = initial_balances
        self.window_duration = window_duration
        self.speed_factor = speed_factor
        self._balances = dict(initial_balances)
        self._running = False
        self._current_window_start = None


    def stop(self):
        self._running = False


    def run(self, obligations: list[Obligation]):
        if not obligations: return

        # Set initial window start to earliest obligation time
        self._running = True
        self._current_window_start = obligations[0].timestamp.replace(second=0, microsecond=0)

        for i, obl in enumerate(obligations):
            if not self._running:
                break
            while obl.timestamp >= self._current_window_start + self.window_duration:
                self._process_window(self._current_window_start + self.window_duration)
                # Advance window start to beginning of next window
                self._current_window_start += self.window_duration

            self.store.add(obl)
            # Simulate real time
            if i + 1 < len(obligations):
                # Calculate sleep based on time until next obligation (scaled)
                next_ts = obligations[i+1].timestamp
                delta = (next_ts - obl.timestamp).total_seconds()
                if delta > 0 and self.speed_factor > 0:
                    time.sleep(delta / self.speed_factor)
    
        # After all obligations, close the final window
        if self.store:
            self._process_window(self._current_window_start + self.window_duration)
        self._running = False


    def _process_window(self, window_end: datetime):
        """Run netting and settlement for the window [start, window_end)"""

        window_start = self._current_window_start
        logger.info(f"Processing window: {window_start} - {window_end}")

        # Extract obligations in this window
        window_obls = self.store.extract_window(window_start, window_end)
        if not window_obls: return

        gross_dict = defaultdict(lambda: defaultdict(deque))
        gross_volume = Decimal(0)
        for obl in window_obls:
            gross_dict[obl.payer][obl.payee].append((obl.tx_id, obl.amount, obl.timestamp))
            gross_volume += obl.amount

        # Bilateral net and multilateral net
        net_edges = bilateral_net(gross_dict)
        net_edges = multilateral_net(net_edges)

        # Settlement
        window_ts = window_start
        net_payments_with_ts = [(payer, payee, amt, window_ts) for payer, payee, amt in net_edges]
        results = settlement_scheduler(net_payments_with_ts, self._balances)
        self._balances = results['final_balances']

        # Calculate metrics
        net_volume = sum(amt for _, _, amt in net_edges)
        liquidity_saved = gross_volume - net_volume
        total_settled = results['total_settled']
        total_failed = results['total_failed']

        # Update snapshot, convert net edges to net positions per participant
        net_positions = defaultdict(Decimal)
        for payer, payee, amt in net_edges:
            net_positions[payer] -= amt
            net_positions[payee] += amt

        self.snapshot.update(
            net_positions=dict(net_positions),
            balances=dict(self._balances),
            total_settled=total_settled,
            total_failed=total_failed,
            liquidity_used=self.snapshot.liquidity_used + total_settled,
            liquidity_saved=liquidity_saved,
            gross_volume=gross_volume,
            failure_rate=results['failure_rate'],
            last_window_end=window_end
        )

        persist_window(
            window_obls=window_obls,
            window_start=window_start,
            window_end=window_end,
            gross_volume=gross_volume,
            net_volume=net_volume,
            liquidity_saved=liquidity_saved,
            net_positions=dict(net_positions),
            settled_payments=results['settled'],
            failed_payments=results['failed'],
            balances=self._balances
        )
