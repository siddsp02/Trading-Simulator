import pytest

from src.main import Account


def test_account_creation() -> None:
    with pytest.raises(ValueError):
        Account(-1)
    with pytest.raises(Exception):
        Account("abab")  # type: ignore
    acc = Account(10_000)
    assert acc.balance == 10_000
    assert acc.orders == acc.trades == []
    assert acc.pnl == 0
    assert acc.realized_pnl == 0
    assert acc.equity == acc.balance
    