"""Test cart totals endpoint."""
import pytest


def test_cart_totals_basic(customer_client):
    resp = customer_client.post('/api/v1/customer/orders/totals', json={
        'items': [
            {'product_id': 1, 'price': 100.0, 'quantity': 2},
            {'product_id': 2, 'price': 50.0, 'quantity': 1}
        ],
        'country': 'OM'
    })
    assert resp.status_code == 200, f"Request failed: {resp.text}"
    data = resp.json()
    assert data['subtotal'] == 250.0
    assert 'total' in data
    assert 'tax_amount' in data
    assert 'shipping' in data
    print(f"Response: {data}")


def test_cart_totals_empty_cart(customer_client):
    resp = customer_client.post('/api/v1/customer/orders/totals', json={
        'items': [],
        'country': 'OM'
    })
    assert resp.status_code == 200, f"Request failed: {resp.text}"
    data = resp.json()
    assert data['subtotal'] == 0.0
    assert data['total'] == 0.0
