import pytest

from src.main import Account, STOCK_PRICES, Action, Order, Status


def test_account_creation() -> None:
    with pytest.raises(ValueError):
        acc = Account(-1)
    with pytest.raises(TypeError):
        acc = Account("abab")  # type: ignore
    acc = Account(10_000.0)
