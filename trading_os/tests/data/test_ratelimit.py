"""TokenBucket timing tests, driven entirely by a fake clock/sleep so the
suite runs instantly (no real sleeping)."""

from __future__ import annotations

import threading

import pytest

from tradingos.data.ratelimit import TokenBucket


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def make_bucket(rate: float, capacity: int) -> tuple[TokenBucket, FakeClock, list[float]]:
    clock = FakeClock()
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.advance(seconds)

    bucket = TokenBucket(rate, capacity, clock=clock, sleep=fake_sleep)
    return bucket, clock, sleeps


def test_burst_capacity_allows_immediate_acquire_up_to_capacity() -> None:
    bucket, clock, sleeps = make_bucket(rate=3.0, capacity=3)
    for _ in range(3):
        bucket.acquire()
    assert sleeps == []  # full burst available up front, no waiting
    assert clock.t == 0.0


def test_rate_honored_after_burst_exhausted() -> None:
    bucket, clock, sleeps = make_bucket(rate=3.0, capacity=3)
    for _ in range(3):
        bucket.acquire()
    bucket.acquire()  # 4th request must wait for a token to regenerate
    assert sleeps == [pytest.approx(1.0 / 3.0)]
    assert clock.t == pytest.approx(1.0 / 3.0)


def test_ten_requests_at_3_per_second_take_correct_total_wait() -> None:
    bucket, clock, _sleeps = make_bucket(rate=3.0, capacity=3)
    for _ in range(10):
        bucket.acquire()
    # 3 free (burst), then 7 more gated at 1/3s each = 7/3s
    assert clock.t == pytest.approx(7.0 / 3.0)


def test_acquire_n_greater_than_one() -> None:
    bucket, _clock, sleeps = make_bucket(rate=3.0, capacity=3)
    bucket.acquire(3)  # exhausts the whole burst in one call
    assert sleeps == []
    bucket.acquire(3)  # needs to wait for all 3 tokens to regenerate
    assert sleeps == [pytest.approx(1.0)]


def test_acquire_more_than_capacity_raises() -> None:
    bucket, _clock, _sleeps = make_bucket(rate=3.0, capacity=3)
    with pytest.raises(ValueError):
        bucket.acquire(4)


def test_acquire_zero_or_negative_raises() -> None:
    bucket, _clock, _sleeps = make_bucket(rate=3.0, capacity=3)
    with pytest.raises(ValueError):
        bucket.acquire(0)


@pytest.mark.parametrize(("rate", "capacity"), [(0, 3), (-1, 3), (3, 0)])
def test_invalid_construction_raises(rate: float, capacity: int) -> None:
    with pytest.raises(ValueError):
        TokenBucket(rate=rate, capacity=capacity)


def test_concurrent_acquire_within_capacity_never_blocks_or_errors() -> None:
    """All 5 threads acquiring 1 token each against a capacity-5 bucket must
    succeed without any sleeping -- exercises the lock under real contention."""
    bucket, _clock, sleeps = make_bucket(rate=100.0, capacity=5)
    results: list[int] = []
    lock = threading.Lock()

    def worker() -> None:
        bucket.acquire()
        with lock:
            results.append(1)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    assert len(results) == 5
    assert sleeps == []
