import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(_BACKEND_ROOT))
os.chdir(str(_BACKEND_ROOT))

FILE_PATH = _BACKEND_ROOT / "middleware" / "security_headers.py"


def test_no_raw_os_getenv_for_urls():
    source = FILE_PATH.read_text(encoding="utf-8")
    assert "os.getenv('BACKEND_URL'" not in source
    assert 'os.getenv("BACKEND_URL"' not in source
    assert "os.getenv('FRONTEND_URL'" not in source
    assert 'os.getenv("FRONTEND_URL"' not in source


def test_hsts_production_only():
    from middleware.security_headers import EnhancedSecurityHeadersMiddleware

    middleware = EnhancedSecurityHeadersMiddleware(None)

    def make_request(scheme, forwarded_proto=None):
        req = MagicMock()
        req.method = "GET"
        req.headers = {}
        if forwarded_proto:
            req.headers["x-forwarded-proto"] = forwarded_proto
        req.url.scheme = scheme
        return req

    def make_response():
        resp = MagicMock()
        resp.headers = {}
        return resp

    async def dispatch(req, resp):
        async def call_next(r):
            return resp
        return await middleware.dispatch(req, call_next)

    import asyncio

    with patch("middleware.security_headers.settings") as mock_settings:
        mock_settings.app_env = "production"
        mock_settings.security_headers_enabled = True
        mock_settings.cors_origins_list = []

        prod_https_req = make_request("https", "https")
        prod_https_resp = make_response()
        prod_https_result = asyncio.run(dispatch(prod_https_req, prod_https_resp))
        assert "Strict-Transport-Security" in prod_https_result.headers

        prod_http_req = make_request("http")
        prod_http_resp = make_response()
        prod_http_result = asyncio.run(dispatch(prod_http_req, prod_http_resp))
        assert "Strict-Transport-Security" not in prod_http_result.headers

    with patch("middleware.security_headers.settings") as mock_settings:
        mock_settings.app_env = "development"
        mock_settings.security_headers_enabled = True
        mock_settings.cors_origins_list = []

        dev_https_req = make_request("https", "https")
        dev_https_resp = make_response()
        dev_https_result = asyncio.run(dispatch(dev_https_req, dev_https_resp))
        assert "Strict-Transport-Security" not in dev_https_result.headers


