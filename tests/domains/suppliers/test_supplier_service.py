import inspect
import sys
import os

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from domains.suppliers.services import supplier_service


def test_list_suppliers_pagination():
    """Verify that supplier service list endpoints expose pagination parameters."""
    # get_supplier_products must accept limit and offset
    sig = inspect.signature(supplier_service.get_supplier_products)
    assert "limit" in sig.parameters
    assert "offset" in sig.parameters

    # list_public_suppliers must accept limit and offset
    sig = inspect.signature(supplier_service.list_public_suppliers)
    assert "limit" in sig.parameters
    assert "offset" in sig.parameters

    # get_public_supplier_products must accept limit and offset
    sig = inspect.signature(supplier_service.get_public_supplier_products)
    assert "limit" in sig.parameters
    assert "offset" in sig.parameters
