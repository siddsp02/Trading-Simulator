import pytest

from src.main import Account


def test_account_creation() -> None:
    with pytest.raises(ValueError):
        acc = Account(-1)
    acc = Account(10_000.0)
