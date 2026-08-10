import random
import uuid
from datetime import datetime, timedelta, timezone
import pandas as pd
from pandas import DataFrame


def generate_participants(n: int = 30) -> list[str]:
    return [f"Bank_{i}" for i in range(n)]


def assign_clusters(participants: list[str], cluster_size: int = 5) -> list:
    clusters = []
    for i in range(0, len(participants), cluster_size):
        cluster = participants[i:i+cluster_size]
        clusters.append(cluster)
    return clusters


def generate_cycle(
        participants: list[str], 
        min_amount: int = 1000, 
        max_amount: int = 100000,
        tz: timezone = timezone.utc
) -> list[tuple[str, str, float, datetime]]:
    length = random.choice([3, 4, 5])
    cycle_nodes = random.sample(participants, length)

    # All edges in this cycle will get same random timestamp within the day
    base_ts = datetime(2026, 7, 15, 8, 0, 0, tzinfo=tz) + timedelta(
        seconds=random.randint(0, 10*60*60 - 1)  # 10 hrs in secs
    )
    edges = []
    for i in range(length):
        payer = cycle_nodes[i]
        payee = cycle_nodes[(i + 1) % length]
        amount = round(random.uniform(min_amount, max_amount), 2)
        edges.append((payer, payee, amount, base_ts))
    return edges


def generate_obligations(
    num_cycles: int = 50, 
    noise_factor: int = 2, 
    start_time: datetime = None,
    end_time: datetime = None,
    tz: timezone = timezone.utc,
    seed: int = None
) -> DataFrame:
    if seed is not None:
        random.seed(seed)
    if start_time is None:
        start_time = datetime(2026, 7, 15, 8, 0, 0, tzinfo=tz)
    if end_time is None:
        end_time = datetime(2026, 7, 15, 18, 0, 0, tzinfo=tz)

    participants = generate_participants()
    clusters = assign_clusters(participants)
    edges = _generate_raw_edges(num_cycles, noise_factor, participants, clusters)
    df = _build_obligation_df(edges, start_time, end_time)
    return df


# -------------- Helpers --------------
def _generate_raw_edges(
    num_cycles: int, 
    noise_factor: int, 
    participants: list[str], 
    clusters: list
) -> list[tuple[str, str, float, datetime | None]]:
    all_obligations = []
    # Generate cycles within clusters
    if num_cycles > 0:
        # Each cluster gets num cycles proportional to cluster size
        cycles_per_cluster = max(1, num_cycles // len(clusters))
        for cluster in clusters:
            for _ in range(cycles_per_cluster):
                cycle_edges = generate_cycle(cluster)
                all_obligations.extend(cycle_edges)

    # Generate random noise (non-cycle payments) within and across clusters
    noise_count = num_cycles * noise_factor
    for _ in range(noise_count):
        payer = random.choice(participants)
        payee = random.choice(participants)
        if payer == payee:
            continue
        amount = round(random.lognormvariate(10, 1.5), 2)
        all_obligations.append((payer, payee, amount, None)) # Assign rand timestamp later

    return all_obligations


def _build_obligation_df(edges: list, start_time: datetime, end_time: datetime) -> DataFrame:
    # Create DataFrame with timestamps
    df = pd.DataFrame(edges, columns=['payer', 'payee', 'amount', 'timestamp'])
    df['currency'] = 'USD'

    # For edges without a timestamp (noise), assign random timestamp
    time_diff_sec = (end_time - start_time).total_seconds()
    mask = df['timestamp'].isnull()
    df.loc[mask, 'timestamp'] = [
        start_time + timedelta(seconds=random.randint(0, int(time_diff_sec))) for _ in range(mask.sum())
    ]

    df = df.sort_values('timestamp')
    
    # Add unique tx_id
    df['tx_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    df = df[['tx_id', 'payer', 'payee', 'amount', 'currency', 'timestamp']]

    return df
