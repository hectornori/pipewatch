"""Tests for pipewatch.retry."""
import pytest

from pipewatch.retry import RetryPolicy, policy_from_dict, with_retry


# ---------------------------------------------------------------------------
# RetryPolicy construction
# ---------------------------------------------------------------------------

def test_default_policy():
    p = RetryPolicy()
    assert p.max_attempts == 3
    assert p.delay_seconds == 5.0
    assert p.backoff_factor == 2.0


def test_policy_invalid_attempts():
    with pytest.raises(ValueError, match="max_attempts"):
        RetryPolicy(max_attempts=0)


def test_policy_invalid_delay():
    with pytest.raises(ValueError, match="delay_seconds"):
        RetryPolicy(delay_seconds=-1)


def test_policy_invalid_backoff():
    with pytest.raises(ValueError, match="backoff_factor"):
        RetryPolicy(backoff_factor=0.5)


def test_policy_from_dict():
    p = policy_from_dict({"max_attempts": 5, "delay_seconds": 1.0, "backoff_factor": 1.5})
    assert p.max_attempts == 5
    assert p.delay_seconds == 1.0
    assert p.backoff_factor == 1.5


def test_policy_from_dict_defaults():
    p = policy_from_dict({})
    assert p.max_attempts == 3


# ---------------------------------------------------------------------------
# with_retry behaviour
# ---------------------------------------------------------------------------

def test_success_on_first_attempt():
    calls = []

    def fn():
        calls.append(1)
        return "ok"

    policy = RetryPolicy(max_attempts=3, delay_seconds=0)
    result = with_retry(fn, policy)
    assert result == "ok"
    assert len(calls) == 1


def test_success_after_retries():
    attempts = []

    def flaky():
        attempts.append(1)
        if len(attempts) < 3:
            raise RuntimeError("not yet")
        return "done"

    policy = RetryPolicy(max_attempts=3, delay_seconds=0)
    result = with_retry(flaky, policy)
    assert result == "done"
    assert len(attempts) == 3


def test_raises_after_all_attempts_exhausted():
    def always_fails():
        raise ValueError("boom")

    policy = RetryPolicy(max_attempts=3, delay_seconds=0, exceptions=(ValueError,))
    with pytest.raises(ValueError, match="boom"):
        with_retry(always_fails, policy)


def test_non_matching_exception_not_retried():
    """Exceptions not in the policy tuple should propagate immediately."""
    calls = []

    def fn():
        calls.append(1)
        raise TypeError("unexpected")

    policy = RetryPolicy(max_attempts=5, delay_seconds=0, exceptions=(ValueError,))
    with pytest.raises(TypeError):
        with_retry(fn, policy)

    assert len(calls) == 1


def test_passes_args_and_kwargs():
    def add(a, b, *, multiplier=1):
        return (a + b) * multiplier

    policy = RetryPolicy(max_attempts=1, delay_seconds=0)
    assert with_retry(add, policy, 3, 4, multiplier=2) == 14
