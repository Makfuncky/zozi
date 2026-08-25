"""Prometheus metrics setup for Zozi Platform."""
from prometheus_client import start_http_server


def setup_prometheus(app=None):
    """Initialize Prometheus metrics endpoint."""
    try:
        from prometheus_client import start_http_server
        start_http_server(9090)
    except OSError:
        # Port already in use
        pass
