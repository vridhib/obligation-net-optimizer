import pytest
import random
import pandas as pd
import networkx as nx
from datetime import datetime, timezone, timedelta
from ..data_generator.generate_obligations import generate_obligations, generate_participants, assign_clusters


# ------------- Fixtures -------------
@pytest.fixture
def participant_cluster():
    """Mapping participant -> cluster index (0..5)"""
    participants = generate_participants(n=30)
    clusters = assign_clusters(participants, 5)
    mapping = {}
    for idx, cluster in enumerate(clusters):
        for p in cluster:
            mapping[p] = idx
    return mapping


# --------------- Tests --------------
def test_default_parameters_return_dataframe():
    df = generate_obligations()
    assert isinstance(df, pd.DataFrame)
    expected_cols = {'payer', 'payee', 'amount', 'currency', 'timestamp'}
    assert set(df.columns) == expected_cols

 
def test_all_amounts_positive():
    df = generate_obligations(num_cycles=5, noise_factor=2)
    assert (df['amount'] > 0).all()


def test_all_currency_are_usd():
    df = generate_obligations()
    assert (df['currency'] == 'USD').all()


def test_timestamps_within_window():
    start = datetime.now(tz=timezone.utc)
    end = datetime.now(tz=timezone.utc) + timedelta(hours=10)
    df = generate_obligations(num_cycles=10, noise_factor=2, start_time=start, end_time=end)
    assert (df['timestamp'] >= start).all()
    assert (df['timestamp'] <= end).all()


def test_timestamps_sorted():
    df = generate_obligations()
    assert df['timestamp'].is_monotonic_increasing


def test_cycles_exist():
    """
    Without noise, the generated graph should contain at least one 
    directed cycle (because every cluster gets cycles).
    """
    df = generate_obligations(num_cycles=20, noise_factor=0)
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(row['payer'], row['payee'], amount=row['amount'])
    cycles = list(nx.simple_cycles(G))
    assert len(cycles) > 0


def test_cycle_participants_belong_to_same_cluster(participant_cluster):
    df = generate_obligations(num_cycles=10, noise_factor=0)
    # For each edge, check that payer and payee are in the same cluster
    for _, row in df.iterrows():
        c_payer = participant_cluster[row['payer']]
        c_payee = participant_cluster[row['payee']]
        assert c_payer == c_payee


def test_noise_introduces_cross_cluster_edges(participant_cluster):
    random.seed(42) # Deterministic noise placement
    # Generate with some noise
    df = generate_obligations(num_cycles=10, noise_factor=2)
    cross_cluster = any(
        participant_cluster[row['payer']] != participant_cluster[row['payee']] for _, row in df.iterrows()
    )
    assert cross_cluster


@pytest.mark.parametrize("num_cycles,noise_factor", [
    (5, 2),
    (20, 3),
    (0, 5)
])
def test_row_count_roughly_matches_cycles_and_noise(num_cycles, noise_factor):
    df = generate_obligations(num_cycles=num_cycles, noise_factor=noise_factor)
    # Cycle edges: each cycle length is between 3 and 5, average ~4
    # Expected ~ num_cycles * 4 + noise_factor * num_cycles
    expected_min = num_cycles * 3 + noise_factor * num_cycles
    expected_max = num_cycles * 5 + noise_factor * num_cycles
    assert expected_min <= len(df) <= expected_max