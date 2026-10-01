import sys
import os

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from domains.catalog.models.products import Product


def test_product_is_deleted_indexed():
    assert Product.__table__.c.is_deleted.index is True
