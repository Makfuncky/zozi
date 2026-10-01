"""Shared kernel - fiscal period / date-range logic (spec: kernel/period.py)."""
from datetime import date, timedelta
from typing import Iterator

def fiscal_quarter(d: date) -> int:
    return (d.month - 1) // 3 + 1

def date_range(start: date, end: date) -> Iterator[date]:
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)
