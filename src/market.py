from dataclasses import InitVar, dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import IntEnum

try:
    from technicals import Action
except ImportError:
    from src.technicals import Action


STOCK_PRICES = {
    "AAPL": Decimal(200),
    "GOOGL": Decimal(200),
    "MSFT": Decimal(400),
}


def get_stock_price(ticker: str) -> Decimal:
    try:
        return STOCK_PRICES[ticker]
    except KeyError:
        raise LookupError(f'Stock with ticker "{ticker}" does not exist.')


class OrderStatus(IntEnum):
    UNFILLED = 0
    PARTIALLY_FILLED = 1
    FILLED = 2


@dataclass
class Order:
    ticker: str
    action: Action
    qty: int = 0
    price: Decimal = field(init=False)
    filled: int = field(init=False, default=0)
    timestamp: float = datetime.now().timestamp()

    def __str__(self) -> str:
        return f"<{self.action.name} {self.ticker} @ {self.price} ({self.filled}/{self.qty} filled)>"

    def __post_init__(self) -> None:
        if self.qty < 0:
            raise ValueError("Can't make an order for a negative amount.")
        if self.action not in Action:
            raise ValueError("Invalid Action.")
        self.price = get_stock_price(self.ticker)

    def fill(self, amount: int | None = None) -> None:
        if amount is None:
            self.filled = self.qty
        else:
            if amount < 0:
                raise ValueError("Amount to fill cannot be negative.")
            if amount > self.remaining:
                raise ValueError("Cannot fill more stocks than remaining in order.")
            self.filled += amount

    def get_size(self, absval: bool = True) -> Decimal:
        return self.size if (self.action == Action.BUY or absval) else -self.size

    @property
    def remaining(self) -> int:
        return self.qty - self.filled

    @property
    def size(self) -> Decimal:
        return self.qty * self.price

    @property
    def status(self) -> OrderStatus:
        if self.filled == self.qty:
            return OrderStatus.FILLED
        if 0 < self.filled < self.qty:
            return OrderStatus.PARTIALLY_FILLED
        return OrderStatus.UNFILLED


@dataclass
class Position:
    ticker: str
    qty: int = 0
    price: Decimal = Decimal()

    def update_from_order(self, order: Order) -> None:
        self.update(order.qty if order.action == Action.BUY else -order.qty)
        order.fill()

    def update(self, qty: int, new_price: Decimal | None = None) -> None:
        if new_price is None:
            new_price = get_stock_price(self.ticker)
        if qty > 0:
            self.price = (self.qty * self.price + qty * new_price) / (self.qty + qty)
        self.qty += qty

    @property
    def pnl(self) -> Decimal:
        price = get_stock_price(self.ticker)
        return self.qty * (price - self.price)

    @property
    def value(self) -> Decimal:
        price = get_stock_price(self.ticker)
        return self.qty * price


@dataclass
class Trade:
    position: InitVar[Position]
    order: Order
    entry_price: Decimal = field(init=False)
    timestamp: float = datetime.now().timestamp()

    def __post_init__(self, position: Position) -> None:
        if position.qty > self.order.qty:
            raise ValueError()
        self.entry_price = position.price

    @property
    def realized_pnl(self) -> Decimal:
        return (self.order.price - self.entry_price) * self.order.qty
