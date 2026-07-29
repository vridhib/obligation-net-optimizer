from collections import deque
from decimal import Decimal


# Using plain dict for `gross` to avoid autovivification of empty inner dicts for payees with no outgoing obligations (because graph is sparse).
def bilateral_net(
        obligations: dict[str, dict[str, deque]]
        ) -> list[tuple[str, str, Decimal]]:
    """Computes the minimum net payment edges between counterparties.

    Args:
        obligations: maps each payer to a dict of payees, where each value is a 
        deque of `(tx_id, amount, timestamp)` tuples.
    
    Returns: 
        A list of `(payer, payee, net_amount)` where net_amount > 0 indicates that
        `payer` owes `payee`. Contradictory edges are eliminated. Self payments 
        (payer == payee) are not expected in the input and are not explicitly handled; 
        the caller is expected to filter them out beforehand.
    """
    gross = {}
    # Aggregate all obligations between each pair
    for payer, payees in obligations.items():
        for payee, deq in payees.items():
            total = sum(amt for (_, amt, _) in deq)
            gross[(payer, payee)] = gross.get((payer, payee), Decimal(0)) + total

    # Compute net per directed pair
    processed_pairs = set()
    netted = []
    for (payer, payee), a_to_b in gross.items():
        # Skip if handled in the other direction
        if (payee, payer) in processed_pairs:
            continue
        processed_pairs.add((payer, payee))

        b_to_a = gross.get((payee, payer), Decimal(0))
        net = a_to_b - b_to_a
        if net > 0:
            netted.append((payer, payee, net))
        elif net < 0:
            netted.append((payee, payer, -net))
        # net == 0: edges are eliminated
    return netted
