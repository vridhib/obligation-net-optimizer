import pytest
from decimal import Decimal
from collections import deque
from ..bilateral import bilateral_net



# Helper to build the nested deque structure
def _make_deq(*amounts):
    """Return a deque of dummy obligations with the given amounts."""
    return deque((f"tx_{i}", amt, None) for i, amt in enumerate(amounts))

# ---------- Fixtures ---------- 
@pytest.fixture
def empty_obligations():
    return {}

@pytest.fixture
def single_directed():
    # BankA owes BankB 100, BankB owes nothing to BankA
    return {"A": {"B": _make_deq(100)}}

@pytest.fixture
def contradictory_pair():
    # A->B: 200,  B->A: 150  -> net: A owes B 50
    return {
        "A": {"B": _make_deq(200)},
        "B": {"A": _make_deq(150)},
    }

@pytest.fixture
def multi_participant():
    # A->B 300, B->C 200, C->A 100, A->C 50
    return {
        "A": {"B": _make_deq(300), "C": _make_deq(50)},
        "B": {"C": _make_deq(200)},
        "C": {"A": _make_deq(100)},
    }


def test_empty_obligations(empty_obligations):
    assert bilateral_net(empty_obligations) == []


def test_single_directed(single_directed):
    result = bilateral_net(single_directed)
    assert result == [("A", "B", Decimal(100))]


def test_contradictory_pair(contradictory_pair):
    result = bilateral_net(contradictory_pair)
    assert len(result) == 1
    assert ("A", "B", Decimal(50)) in result


def test_net_zero_results_in_no_edge():
    # A->B 100, B->A 100 -> nothing
    ob = {
        "A": {"B": _make_deq(100)},
        "B": {"A": _make_deq(100)},
    }
    assert bilateral_net(ob) == []

def test_multi_participant(multi_participant):
    result = bilateral_net(multi_participant)
    # Expected: A->B 300, B->C 200, C->A 100, A->C 50
    # after netting:
    # A->B: 300 (B->A = 0) -> 300
    # B->C: 200 (C->B = 0) -> 200
    # C->A: 100 vs A->C 50  -> net C->A 50
    expected = [
        ("A", "B", Decimal(300)),
        ("B", "C", Decimal(200)),
        ("C", "A", Decimal(50)),
    ]
    assert sorted(result) == sorted(expected)


def test_preserves_decimal_type():
    ob = {"A": {"B": _make_deq(10)}}
    result = bilateral_net(ob)
    assert isinstance(result[0][2], Decimal)


def test_does_not_modify_input():
    ob = {"A": {"B": _make_deq(100)}}
    _ = bilateral_net(ob)
    # check that ob is unchanged (deque still there)
    assert "A" in ob
    assert "B" in ob["A"]


@pytest.mark.parametrize(
    "a_to_b, b_to_a, expected",
    [
        (200, 50, ("A", "B", 150)),  # net A->B
        (50, 200, ("B", "A", 150)),  # net B->A
        (100, 100, None),            # net zero
    ],
)
def test_pairwise_netting(a_to_b, b_to_a, expected):
    ob = {
        "A": {"B": _make_deq(a_to_b)},
        "B": {"A": _make_deq(b_to_a)},
    }
    result = bilateral_net(ob)
    if expected is None:
        assert result == []
    else:
        assert result == [expected]