from datetime import datetime
from decimal import Decimal
from .models import NettingWindow, NetPosition, SettlementAttempt, ParticipantBalance, Obligation


def persist_window(
    window_obls: list[Obligation],
    window_start: datetime,
    window_end: datetime, 
    gross_volume: Decimal,
    net_volume: Decimal,
    liquidity_saved: Decimal,
    net_positions: dict[str, Decimal],
    settled_payments: list[tuple[str, str, Decimal]],
    failed_payments: list[tuple[str, str, Decimal]],
    balances: dict[str, Decimal]
) -> None:
    # Netting window
    window = NettingWindow.objects.create(
        start_time=window_start,
        end_time=window_end,
        gross_obligation_count=len(window_obls),
        net_obligation_count=len(settled_payments) + len(failed_payments),
        gross_volume=gross_volume,
        net_volume=net_volume,
        liquidity_saved=liquidity_saved
    )

    # Net positions
    for participant, net_amt in net_positions.items():
        NetPosition.objects.create(window=window, participant=participant, net_amount=net_amt)

    # Settlement attempts
    for payer, payee, amt in settled_payments:
        SettlementAttempt.objects.create(window=window, payer=payer, payee=payee, amount=amt, status='settled')
    for payer, payee, amt in failed_payments:
        SettlementAttempt.objects.create(window=window, payer=payer, payee=payee, amount=amt, status='failed')

    # Update participants' balances
    for participant, balance in balances.items():
        ParticipantBalance.objects.update_or_create(participant=participant, defaults={'balance': balance})
