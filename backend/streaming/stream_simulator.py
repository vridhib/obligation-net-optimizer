import time
import logging
import threading
import pandas as pd
import matplotlib.pyplot as plt
from django.utils import timezone as django_timezone
from datetime import datetime, timedelta, timezone
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
                'net_positions': dict(self.net_positions),
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


    def generate_report(self, output_path="report.png"):
        if not self.window_history:
            logger.warning("No window history available for report.")
            return None

        gross_per_window = sum(w['gross_volume'] for w in self.window_history)
        settled_per_window = sum(w['total_settled'] for w in self.window_history)
        print(f"Total gross: {gross_per_window}, Total settled: {settled_per_window}")

        df = pd.DataFrame(self.window_history)
        df['last_window_end'] = pd.to_datetime(df['last_window_end'])
        df.set_index('last_window_end', inplace=True)

        # Convert Decimal columns to float for plotting
        numeric_cols = ['total_settled', 'total_failed', 'liquidity_used', 'liquidity_saved', 'gross_volume', 'failure_rate']
        for col in numeric_cols:
            df[col] = df[col].astype(float)

        _, axes = plt.subplots(3, 2, figsize=(14, 14))

        # Volume & savings (top left)
        df[['gross_volume', 'total_settled', 'liquidity_saved']].plot(
            ax=axes[0, 0], title="Gross vs Settled Volume & Liquidity Saved"
        )

        # Failure rate (top right)
        df[['failure_rate']].plot(ax=axes[0, 1], title="Settlement Failure Rate", color='red')

        # Settlement composition (middle left) stacked bar
        comp_df = df[['total_settled', 'total_failed']].copy()
        comp_df.plot.bar(ax=axes[1, 0], stacked=True, title="Settled vs Failed per Window")

        # Liquidity usage trend (middle right) cumulative
        df['liquidity_used_cum'] = df['liquidity_used']  # already cumulative
        df['liquidity_used_cum'].plot(ax=axes[1, 1], title="Cumulative Liquidity Used", color='green')

        # Final net positions (bottom left) bar chart with color
        if self.net_positions:
            net_df = pd.DataFrame(
                list(self.net_positions.items()), columns=['Participant', 'Net Position']
            )
            colors = ['green' if v >= 0 else 'red' for v in net_df['Net Position']]
            axes[2, 0].bar(net_df['Participant'], net_df['Net Position'], color=colors)
            axes[2, 0].set_title("Final Net Positions (Green = Creditor, Red = Debtor)")
            axes[2, 0].axhline(y=0, color='black', linewidth=0.8)

        # Final balances (bottom right)
        if self.balances:
            bal_df = pd.DataFrame(
                list(self.balances.items()), columns=['Participant', 'Balance']
            )
            axes[2, 1].bar(bal_df['Participant'], bal_df['Balance'])
            axes[2, 1].set_title("Final Balances")

        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return df


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


    def load_csv(self, csv_path: str) -> list[Obligation]:
        try:
            df = pd.read_csv(csv_path, parse_dates=['timestamp'])
            df.sort_values('timestamp', inplace=True)
        except pd.errors.EmptyDataError:
            return []

        obligations = []
        for row in df.itertuples():
            ts = row.timestamp.to_pydatetime()
            if django_timezone.is_naive(ts):
                ts = django_timezone.make_aware(ts, timezone=timezone.utc)
            obligations.append(
                Obligation(
                    tx_id=str(row.tx_id),
                    payer=row.payer,
                    payee=row.payee,
                    timestamp=ts,
                    amount=Decimal(str(row.amount)),
                )
            )
        return obligations


    def stop(self):
        self._running = False


    def run(self, csv_path: str):
        # Load CSV
        obligations = self.load_csv(csv_path)
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


    # TODO: refactor _process_window
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
            balances=self._balances,
        )
