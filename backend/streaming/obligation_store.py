import threading
from collections import deque
from datetime import datetime
from typing import NamedTuple
from decimal import Decimal


class Obligation(NamedTuple):
    tx_id: str
    payer: str
    payee: str
    timestamp: datetime
    amount: Decimal


class ObligationStore:
    """
    Thread-safe and time-ordered store of pending obligations.

    Uses a deque to maintain insertion order (which is assumed to be 
    chronological). Window extraction scans from the left to avoid full 
    list copies. Lock protects all read and write operations for concurrent 
    access.
    """

    def __init__(self):
        self._deque = deque()
        self._lock = threading.Lock()


    def add(self, obligation: Obligation) -> None:
        with self._lock:
            self._deque.append(obligation)


    def extend(self, obligations: list[Obligation]) -> None:
        with self._lock:
            self._deque.extend(obligations)


    def extract_window(self, start: datetime, end: datetime) -> list[Obligation]:
        """
        Remove and return all obligations with timestamp in [start, end). This 
        assumes the deque is sorted by timestamp and all elements left of start 
        have already been removed. Pop from the left until we see an obligation 
        with timestamp >= end.
        """
        with self._lock:
            window = []
            while self._deque and start <= self._deque[0].timestamp < end:
                window.append(self._deque.popleft())
        return window


    def expire_before(self, cutoff: datetime):
        """
        Remove obligations older than the cutoff and return the count of 
        removed obligations
        """ 
        with self._lock:
            removed = 0
            while self._deque and self._deque[0].timestamp < cutoff:
                self._deque.popleft()
                removed += 1
        return removed


    def __len__(self):
        with self._lock:
            return len(self._deque)
