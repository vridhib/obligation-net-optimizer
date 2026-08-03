import networkx as nx
from ..scc import tarjan_scc, multilateral_net
from ..bilateral import bilateral_net
from decimal import Decimal
import pytest
from collections import defaultdict

# ------------------ Tarjan Tests ------------------
def test_tarjan_empty_graph():
    assert tarjan_scc({}) == []


def test_tarjan_single_node():
    G = {"A": []}
    sccs = tarjan_scc(G)
    assert sccs == [["A"]]


def test_tarjan_self_loop():
    G = {"A": ["A"]}
    sccs = tarjan_scc(G)
    # Self‑loop makes a single‑node SCC
    assert sccs == [["A"]]


def test_tarjan_linear_dag():
    G = {"A": ["B"], "B": ["C"], "C": []}
    sccs = tarjan_scc(G)
    # Each node its own SCC
    assert sorted(map(sorted, sccs)) == [["A"], ["B"], ["C"]]


def test_tarjan_two_disconnected_nodes():
    G = {"A": [], "B": []}
    sccs = tarjan_scc(G)
    result = sorted(map(sorted, sccs))
    assert result == [["A"], ["B"]]


def test_tarjan_matches_networkx():
    # Simple graph with two cycles
    G = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A", "D"],
        "D": ["E"],
        "E": ["D"]
    }
    sccs = tarjan_scc(G)
    # networkx reference
    G_nx = nx.DiGraph(G)
    ref = [set(c) for c in nx.strongly_connected_components(G_nx)]

    # Compare sets of sets
    result_sets = [set(scc) for scc in sccs]
    assert sorted(map(sorted, result_sets)) == sorted(map(sorted, ref))


def test_tarjan_bidirectional_edge_is_scc():
    G = {"A": ["B"], "B": ["A"]}
    sccs = tarjan_scc(G)
    assert sorted(map(sorted, sccs)) == [["A", "B"]]


@pytest.mark.parametrize("n", [1, 5, 20])
def test_tarjan_all_isolated_nodes(n):
    G = {f"Node{i}": [] for i in range(n)}
    sccs = tarjan_scc(G)
    assert len(sccs) == n
    assert all(len(scc) == 1 for scc in sccs)


# ------------- Multilateral Net Tests -------------
def test_multilateral_empty():
    assert multilateral_net([]) == []


def test_multilateral_single_edge_no_cycle():
    # A -> B 100, no cycle -> unchanged
    edges = [("A", "B", Decimal(100))]
    result = multilateral_net(edges)
    assert result == edges


def test_multilateral_simple_cycle():
    # A -> B 100, B -> C 80, C -> A 50
    edges = [
        ("A", "B", Decimal(100)),
        ("B", "C", Decimal(80)),
        ("C", "A", Decimal(50))
    ]
    result = multilateral_net(edges)
    # After netting, there should be at most 2 edges (hub settlement) instead of 3
    assert len(result) <= 3
    assert set(result) != set(edges)


def test_multilateral_perserves_net_balances():
    # Total net obligation (in - out) per participant must not change
    # define edges
    edges = [
        ("A", "B", Decimal(300)),
        ("B", "C", Decimal(200)),
        ("C", "A", Decimal(100)),
        ("A", "C", Decimal(50))
    ]
    result = multilateral_net(edges)
    
    # helper net balance for edges
    def net_balances(edge_list):
        balances = defaultdict(Decimal)
        for u, v, amt in edge_list:
            balances[u] -= amt
            balances[v] += amt
        return balances

    old_balance = net_balances(edges)
    new_balance = net_balances(result)
    for node in set(old_balance) | set(new_balance):
        assert old_balance[node] == new_balance[node]


def test_multilateral_no_cycle_dag():
    edges = [
        ("A", "B", Decimal(100)),
        ("B", "C", Decimal(200)),
        ("A", "C", Decimal(150))
    ]
    result = multilateral_net(edges)
    assert len(edges) == len(result)
    assert set(edges) == set(result)


def test_multilateral_multiple_cycles():
    # Two separate cycles: (A,B) and (C,D,E)
    # gross_edges = [
    #     ("A", "B", Decimal(100)),
    #     ("B", "A", Decimal(80)),
    #     ("C", "D", Decimal(50)),
    #     ("D", "E", Decimal(60)),
    #     ("E", "C", Decimal(40)),
    # ]
    # Manually compute bilateral_net edges result
    net_edges = [
        ("A", "B", Decimal(20)),
        ("C", "D", Decimal(50)),
        ("D", "E", Decimal(60)),
        ("E", "C", Decimal(40))
    ]

    result = multilateral_net(net_edges)
    
    # A net = -20, C net = -10, D net = -10, E net = +20
    # A -> B = 20, C -> E = 10, D -> E = 10
    expected = [("A", "B", Decimal(20)), ("D", "E", Decimal(10)), ("C", "E", Decimal(10))]
    assert result == expected

    for u, v, _ in result:
        assert u != v
    assert len(result) <= 4
    assert len(result) < len(net_edges)
