import heapq
from copy import deepcopy
from decimal import Decimal
from typing import Any
from datetime import datetime


def settlement_scheduler(
        net_payments: list[tuple[str, str, Decimal, datetime]], 
        initial_balances: dict[str, Decimal]
) -> dict[str, Any]:
    """
    Settle net payments using a liquidity-aware priority queue.

    Payments are processed in descending amount order. If a payer lacks funds, the payment is retried once after payments have been attempted.

    Args:
        net_payments: list of (payer, payee, amount, timestamp) with amount > 0.
        initial_balances: dict mapping a participant to available liquidity.

    Returns:
        A dict with keys:
            'settled': list of (payer, payee, amount)
            'failed': list of (payer, payee, amount)
            'final_balances': dict of participant -> remaining balance
            'total_settled': Decimal sum of settled amounts
            'total_failed': Decimal sum of failed amounts
            'failure_rate': Decimal ratio (0 to 1)
    """
    balances = deepcopy(initial_balances)
    heap = []

    for payer, payee, amt, ts in net_payments:
        heapq.heappush(heap, (ts.timestamp(), -amt, payer, payee))

    settled = []
    failed = []

    # First pass
    while heap:
        (_, neg_amt, payer, payee) = heapq.heappop(heap)
        amt = -neg_amt
        if balances.get(payer, Decimal(0)) >= amt:
            balances[payer] -= amt
            balances[payee] += amt
            settled.append((payer, payee, amt))
        else:
            failed.append((payer, payee, amt))

    # Second pass
    still_failed = []
    for payer, payee, amt in failed:
        if balances.get(payer, Decimal(0)) >= amt:
            balances[payer] -= amt
            balances[payee] += amt
            settled.append((payer, payee, amt))
        else:
            still_failed.append((payer, payee, amt))

    # Compute metrics
    total_settled = sum(amt for _, _, amt in settled)
    total_failed = sum(amt for _, _, amt in still_failed)
    total_volume = total_settled + total_failed
    failure_rate = total_failed / total_volume if total_volume else 0

    return {
        'settled': settled,
        'failed': still_failed,
        'final_balances': dict(balances),
        'total_settled': total_settled,
        'total_failed': total_failed,
        'failure_rate': failure_rate
    }