"""Regression test for the orders write-service shim re-wire.

`services.orders.orders_write_service` is a lazy re-export shim. Three ORM row-writer
symbols (`create_order`, `create_order_item`, `update_order`) were stubbed with
`_missing_symbol` but their real implementations exist in the canonical
`services.orders.orders_write_service` module. This test guards that the shim
resolves them to the real functions (and that no `_missing_symbol` stub remains).
"""
from __future__ import annotations

import pytest

import services.orders.orders_write_service as canon
import services.orders.orders_write_service as shim

_REWIRED = ["create_order", "create_order_item", "update_order"]


@pytest.mark.parametrize("name", _REWIRED)
def test_orders_shim_resolves_to_canonical(name):
    assert getattr(shim, name) is getattr(canon, name)


def test_orders_shim_has_no_missing_symbol_helper():
    assert not hasattr(shim, "_missing_symbol")
