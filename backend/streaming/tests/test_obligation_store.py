import threading
import pytest
from datetime import datetime
from decimal import Decimal
from streaming.obligation_store import ObligationStore, Obligation


# ------------- Fixtures -------------
@pytest.fixture
def init_obl_store():
    store = ObligationStore()
    return store

@pytest.fixture
def set_up_obl_store(init_obl_store):
    obls = [
        make_obl("1", "A", "B", "2026-07-15T08:00:00"),
        make_obl("2", "C", "D", "2026-07-15T08:00:30"),
        make_obl("3", "E", "F", "2026-07-15T08:01:00")
    ]
    init_obl_store.extend(obls)
    return init_obl_store


# ------------- Helpers --------------
# Create obligations with a simple factory
def make_obl(tx_id, payer, payee, timestamp_str, amount="100.00"):
    ts = datetime.fromisoformat(timestamp_str)
    return Obligation(tx_id, payer, payee, ts, Decimal(amount))


# -------------- Tests ---------------
def test_add(init_obl_store):
    obl = make_obl("1", "A", "B", "2026-07-15T08:00:00")
    init_obl_store.add(obl)
    assert len(init_obl_store) == 1


def test_extend(init_obl_store):
    obls = [make_obl(str(i), "A", "B", f"2026-07-15T08:00:0{i}") for i in range(5)]
    init_obl_store.extend(obls)
    assert len(init_obl_store) == 5


def test_extract_window_exact_boundary(set_up_obl_store):
    extracted = set_up_obl_store.extract_window(
        datetime.fromisoformat("2026-07-15T08:00:00"), 
        datetime.fromisoformat("2026-07-15T08:01:00")
    )
    assert len(extracted) == 2
    assert extracted[0].tx_id == "1"
    assert extracted[1].tx_id == "2"
    assert len(set_up_obl_store) == 1


def test_extract_window_no_match(set_up_obl_store):
    extracted = set_up_obl_store.extract_window(
        datetime.fromisoformat("2026-07-15T09:00:00"), 
        datetime.fromisoformat("2026-07-15T09:01:00")
    )
    assert len(extracted) == 0
    assert len(set_up_obl_store) == 3


def test_extract_window_empty_store(init_obl_store):
    assert init_obl_store.extract_window(datetime.min, datetime.max) == []


def test_expire_before_removed_non_empty(set_up_obl_store):
    removed = set_up_obl_store.expire_before(
        datetime.fromisoformat("2026-07-15T08:01:00")
    )
    assert removed == 2
    assert len(set_up_obl_store) == 1


def test_expire_before_removed_empty(set_up_obl_store):
    removed = set_up_obl_store.expire_before(
        datetime.fromisoformat("2026-07-15T07:59:00")
    )
    assert removed == 0
    assert len(set_up_obl_store) == 3


def test_thread_safety_concurrent_add_extract(init_obl_store):
    def adder():
        for i in range(100):
            init_obl_store.add(make_obl(str(i), "A", "B", "2026-07-15T08:00:00"))
    threads = [threading.Thread(target=adder) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # All 400 obligations should be present
    assert len(init_obl_store) == 400
    # Extract and check no duplicates
    all_tx = init_obl_store.extract_window(datetime.min, datetime.max)
    assert len(all_tx) == 400
