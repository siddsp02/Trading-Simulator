from collections import deque
from enum import IntEnum
from functools import partial
from math import nan
from statistics import mean
from typing import Iterable, Iterator


class Action(IntEnum):
    BUY = 0
    SELL = 1


def moving_avg(
    it: Iterable[float], n: int = 10, default: float = nan
) -> Iterable[float]:
    window = deque([default] * n, maxlen=n)
    for value in it:
        window.append(value)
        yield mean(window)


def multi_moving_avg(
    it: Iterable[float], periods: list[int] | None = None
) -> Iterator[tuple[float, ...]]:
    if periods is None:
        periods = []
    yield from zip(*map(partial(moving_avg, it), periods))
