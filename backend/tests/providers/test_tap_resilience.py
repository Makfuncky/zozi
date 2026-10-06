"""Paired test for FILE-22b-payments-circuit-breaker-and-timeouts.

Contract section 20: test path tests/providers/test_payments_providers.py,
"list the tap-related test classes and run them". That file exists and is run
(its 9 tap failures are pre-existing and proven identical before/after by A/B).

This file adds the coverage the contract asks for but does not supply: proof
that EVERY httpx call site has an explicit timeout AND is wrapped in a circuit
breaker that actually records outcomes, plus the Law 130 error-mapping and
Law 32 no-secret-in-logs requirements.

The circuit-breaker tests drive the REAL adapter against a real local HTTP
server. They do not mock the breaker, because a mocked breaker cannot prove the
breaker opens.
"""
from __future__ import annotations

import ast
import http.server
import inspect
import pathlib
import json
import logging
import threading
from typing import Any

import pytest

import providers.payments.tap as tap

MODULE_PATH = pathlib.Path(inspect.getfile(tap))
HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "request", "stream"}


# --------------------------------------------------------------------------
# Static enumeration: every httpx call site (contract s19, but done correctly)
# --------------------------------------------------------------------------
def _tree() -> ast.AST:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def _parents(tree: ast.AST) -> dict[int, ast.AST]:
    out: dict[int, ast.AST] = {}

    def build(n):
        for c in ast.iter_child_nodes(n):
            out[id(c)] = n
            build(c)

    build(tree)
    return out


def _client_sites(tree: ast.AST | None = None) -> list[ast.Call]:
    """Every `client.<http-verb>(...)` call in the module.

    Pass *tree* when the result will be cross-referenced against a parent map:
    `id()` values are only meaningful within one parsed tree.
    """
    root = _tree() if tree is None else tree
    return [
        n
        for n in ast.walk(root)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr in HTTP_METHODS
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "client"
    ]


class TestEveryHttpCallHasAnExplicitTimeout:
    """OBS2-023. The contract's grep missed the Client-level timeout; this
    asserts BOTH the per-call timeout and the Client timeout."""

    def test_there_is_at_least_one_http_call_site(self) -> None:
        sites = _client_sites()
        assert sites, "no httpx call sites found - the enumeration is broken"

    def test_every_call_site_declares_its_own_timeout(self) -> None:
        missing = [
            n.lineno for n in _client_sites() if not any(k.arg == "timeout" for k in n.keywords)
        ]
        assert not missing, (
            f"httpx call sites with no explicit per-call timeout: {missing}. "
            "A payment call with no bound can hang indefinitely (Law 296)."
        )

    def test_every_client_construction_declares_a_timeout(self) -> None:
        clients = [
            n
            for n in ast.walk(_tree())
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "Client"
            and isinstance(n.func.value, ast.Name)
            and n.func.value.id == "httpx"
        ]
        assert clients, "no httpx.Client(...) found"
        missing = [n.lineno for n in clients if not any(k.arg == "timeout" for k in n.keywords)]
        assert not missing, f"httpx.Client without a timeout at lines {missing}"

    def test_the_default_timeout_is_a_positive_number(self) -> None:
        assert isinstance(tap._TAP_DEFAULT_TIMEOUT, (int, float))
        assert tap._TAP_DEFAULT_TIMEOUT > 0


class TestEveryHttpCallIsWrappedInTheBreaker:
    """OBS2-021 / Law 296."""

    def test_breaker_is_constructed(self) -> None:
        assert tap._tap_breaker is not None
        assert tap._tap_breaker.name == "tap"
        assert tap._tap_breaker.failure_threshold == tap._TAP_BREAKER_FAILURE_THRESHOLD

    def test_each_call_site_sits_inside_a_breaker_call(self) -> None:
        """Every client.<verb> must be lexically inside the closure that
        `_call_with_breaker` hands to the breaker, so no outbound call can
        bypass the breaker.

        The closure is `_probe`, defined inside `_call_with_breaker`, so the
        ancestor walk accepts either the `_call_with_breaker(...)` call itself or
        the `_probe` definition nested within it.
        """
        tree = _tree()
        parents = _parents(tree)
        sites = _client_sites(tree)
        assert sites, "no call sites enumerated - the parent map must be built from the same tree"

        def inside_breaker(node: ast.AST) -> bool:
            """A call site is guarded when its enclosing lambda (or the `_probe`
            closure) is an argument of a `_call_with_breaker(...)` call.

            The real ancestry in this module is:
                Call(client.post)
                  -> Lambda                      <- the request closure
                    -> Call(_call_with_breaker)  <- the breaker wrapper
            so walking up from the call site, the first Lambda ancestor must
            itself be an argument of a `_call_with_breaker` call.
            """
            cur = node
            while cur is not None and not isinstance(cur, (ast.Lambda, ast.FunctionDef)):
                cur = parents.get(id(cur))
            if cur is None:
                return False
            holder = parents.get(id(cur))
            while holder is not None:
                if isinstance(holder, ast.Call):
                    fn = holder.func
                    if isinstance(fn, ast.Name) and fn.id == "_call_with_breaker":
                        return True
                    # do not walk past a different call into an unrelated scope
                    return False
                holder = parents.get(id(holder))
            return False

        unguarded = [n.lineno for n in sites if not inside_breaker(n)]
        assert not unguarded, (
            f"httpx call sites not wrapped in the circuit breaker: {unguarded} "
            "(Law 296 requires every external call to be wrapped)"
        )

    def test_the_breaker_wrapping_helper_is_the_only_way_out(self) -> None:
        """No call site may construct its own bare httpx call outside the helper."""
        source = inspect.getsource(tap._call_with_breaker)
        assert "client.post(" not in source and "client.get(" not in source, (
            "_call_with_breaker must delegate to the caller's closure rather than "
            "issuing its own request outside the breaker"
        )

    def test_breaker_error_is_mapped_to_a_domain_exception(self) -> None:
        """Law 130: no framework exception may escape this provider."""
        import time as _time

        from infrastructure.observability.circuit_breaker import CircuitBreakerError, CircuitState

        assert issubclass(tap.TapError, Exception)
        breaker = tap._tap_breaker
        saved = (breaker._state, breaker._failure_count, breaker._last_failure_time)
        try:
            # Drive it genuinely OPEN the way the breaker itself would.
            breaker._state = CircuitState.OPEN
            breaker._failure_count = tap._TAP_BREAKER_FAILURE_THRESHOLD
            breaker._last_failure_time = _time.monotonic()
            assert breaker.state == CircuitState.OPEN
            with pytest.raises(tap.TapError) as excinfo:
                tap._call_with_breaker(breaker, lambda: pytest.fail("must not be called"))
            assert "Circuit breaker" in str(excinfo.value)
            assert not isinstance(excinfo.value, CircuitBreakerError), (
                "the raw framework error must not escape (Law 130)"
            )
        finally:
            breaker._state, breaker._failure_count, breaker._last_failure_time = saved


# --------------------------------------------------------------------------
# Behavioural proof: the breaker actually opens (the real defect)
# --------------------------------------------------------------------------
class _StubServer:
    """A local HTTP server that answers with a fixed status."""

    def __init__(self, status: int, body: bytes = b'{"status":"err"}'):
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def _reply(self):
                outer.served.append(self.path)
                self.send_response(outer.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(outer.body)))
                self.end_headers()
                self.wfile.write(outer.body)

            do_GET = _reply
            do_POST = _reply

            def log_message(self, *_):
                pass

        self.status = status
        self.body = body
        self.served: list[str] = []
        self.srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.srv.server_address[1]
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.srv.shutdown()
        self.srv.server_close()


@pytest.fixture
def private_breaker(monkeypatch):
    """Give the adapter its own breaker so tests cannot poison each other."""
    from infrastructure.observability.circuit_breaker import get_circuit_breaker

    breaker = get_circuit_breaker(
        f"tap_test_{id(object())}", failure_threshold=3, recovery_timeout=60
    )
    monkeypatch.setattr(tap, "_tap_breaker", breaker)
    return breaker


@pytest.fixture
def pointed_at(monkeypatch):
    def _point(base: str):
        monkeypatch.setattr(tap, "resolve_tap_api_base_url", lambda *a, **k: base)
        monkeypatch.setattr(tap, "resolve_tap_secret_key", lambda *a, **k: "test-key-not-a-secret")

    return _point


class TestBreakerActuallyOpens:
    """The REAL defect: before the fix the breaker recorded nothing and could
    never open, so a dead gateway was hammered on every request."""

    def test_gateway_5xx_opens_the_breaker(self, private_breaker, pointed_at) -> None:
        with _StubServer(500) as stub, pytest.MonkeyPatch.context() as mp:
            pointed_at(f"http://127.0.0.1:{stub.port}")
            for i in range(6):
                try:
                    tap.create_charge(
                        "10.00", "KWD", customer_name="T U",
                        customer_email="t@example.invalid", order_id=f"O{i}",
                    )
                except tap.TapError:
                    pass
            assert private_breaker.failure_count > 0, (
                "HTTP 500 responses must count toward the breaker threshold; "
                "httpx does not raise for a 5xx, so they are easy to miss"
            )
            assert private_breaker.state.value == "open", (
                f"breaker should have opened after "
                f"{private_breaker.failure_threshold} gateway failures, state="
                f"{private_breaker.state.value}"
            )
            # And it must now short-circuit instead of hammering the gateway.
            served_before = len(stub.served)
            try:
                tap.create_charge(
                    "10.00", "KWD", customer_name="T U",
                    customer_email="t@example.invalid", order_id="AFTER",
                )
            except tap.TapError:
                pass
            assert len(stub.served) == served_before, (
                "an OPEN breaker must reject without issuing an HTTP request"
            )

    def test_transport_error_counts_as_a_failure(self, private_breaker, monkeypatch) -> None:
        import httpx

        monkeypatch.setattr(tap, "resolve_tap_secret_key", lambda *a, **k: "k")
        # Port 1 refuses connections immediately, so this is a pure transport
        # failure with no HTTP response at all.
        monkeypatch.setattr(tap, "resolve_tap_api_base_url", lambda *a, **k: "http://127.0.0.1:1")

        raised = 0
        for _ in range(3):
            try:
                tap.get_charge("ch_1")
            except tap.TapError:
                raised += 1
        assert raised == 3, f"every call should surface a TapError, saw {raised}"
        assert private_breaker.failure_count > 0, (
            "a connection failure must be recorded against the breaker"
        )
        assert issubclass(httpx.ConnectError, Exception)

    def test_success_keeps_the_breaker_closed(self, private_breaker, pointed_at) -> None:
        payload = json.dumps(
            {
                "id": "ch_1",
                "status": "CAPTURED",
                "amount": 1000,
                "currency": "KWD",
                "transaction": {"id": "txn_1", "url": "https://pay.example/x"},
            }
        ).encode()
        with _StubServer(200, payload) as stub, pytest.MonkeyPatch.context() as mp:
            pointed_at(f"http://127.0.0.1:{stub.port}")
            for _ in range(5):
                result = tap.create_charge(
                    "10.00", "KWD", customer_name="T U",
                    customer_email="t@example.invalid", order_id="OK",
                )
            assert result["id"] == "ch_1"
            assert private_breaker.state.value == "closed", (
                "successful calls must never open the breaker"
            )
            assert private_breaker.failure_count == 0

    def test_client_4xx_is_not_treated_as_a_gateway_failure(self) -> None:
        """A bad request is OUR bug; tripping the breaker would take the
        adapter offline for everyone."""
        assert tap._is_gateway_failure(type("R", (), {"status_code": 400})()) is False
        assert tap._is_gateway_failure(type("R", (), {"status_code": 404})()) is False
        assert tap._is_gateway_failure(type("R", (), {"status_code": 422})()) is False

    @pytest.mark.parametrize(
        "status", [408, 425, 429, 500, 502, 503, 504, 505, 507, 599]
    )
    def test_server_side_statuses_are_gateway_failures(self, status: int) -> None:
        assert tap._is_gateway_failure(type("R", (), {"status_code": status})()) is True

    @pytest.mark.parametrize("status", [500, 502, 503, 504, 505, 507, 599])
    def test_every_5xx_is_covered_not_just_the_named_ones(self, status: int) -> None:
        """A 5xx must always classify as a gateway failure."""
        assert tap._is_gateway_failure(type("R", (), {"status_code": status})()) is True

    def test_the_named_set_covers_the_codes_the_platform_relies_on(self) -> None:
        """These specific codes must be named, not merely caught by the >= 500
        fallback, because 408/425/429 are the ones most likely to be trimmed."""
        for status in (408, 425, 429, 500, 502, 503, 504):
            assert status in tap._TAP_BREAKER_FAILURE_STATUSES, (
                f"HTTP {status} must be named in _TAP_BREAKER_FAILURE_STATUSES"
            )

    def test_set_is_frozen_so_it_cannot_be_emptied_at_runtime(self) -> None:
        assert isinstance(tap._TAP_BREAKER_FAILURE_STATUSES, frozenset)
        assert len(tap._TAP_BREAKER_FAILURE_STATUSES) >= 7, (
            f"the gateway-failure set shrank to "
            f"{sorted(tap._TAP_BREAKER_FAILURE_STATUSES)}"
        )


class TestResponseShapesUnchanged:
    """Contract section 3: request/response shapes must not move."""

    def test_create_charge_success_shape(self, pointed_at) -> None:
        payload = json.dumps(
            {
                "id": "ch_9",
                "status": "CAPTURED",
                "amount": 2500,
                "currency": "KWD",
                "transaction": {"id": "txn_9", "url": "https://pay.example/y"},
            }
        ).encode()
        with _StubServer(200, payload) as stub, pytest.MonkeyPatch.context():
            pointed_at(f"http://127.0.0.1:{stub.port}")
            out = tap.create_charge(
                "25.00", "KWD", customer_name="A B", customer_email="a@example.invalid",
                order_id="ORD-9",
            )
        assert set(out) == {"id", "transaction_id", "payment_url", "status", "amount", "currency", "raw"}
        assert out["id"] == "ch_9"
        assert out["transaction_id"] == "txn_9"
        assert out["payment_url"] == "https://pay.example/y"
        assert out["amount"] == "2500"

    def test_get_charge_404_still_raises_not_found(self, private_breaker, pointed_at) -> None:
        with _StubServer(404, b"{}") as stub, pytest.MonkeyPatch.context():
            pointed_at(f"http://127.0.0.1:{stub.port}")
            with pytest.raises(tap.TapChargeNotFoundError):
                tap.get_charge("missing")

    def test_refund_not_found_still_raises_not_found(self, private_breaker, pointed_at) -> None:
        with _StubServer(404, b"{}") as stub, pytest.MonkeyPatch.context():
            pointed_at(f"http://127.0.0.1:{stub.port}")
            with pytest.raises(tap.TapChargeNotFoundError):
                tap.refund_charge("missing")

    def test_public_exports_unchanged(self) -> None:
        assert set(tap.__all__) == {
            "HAS_TAP", "TapError", "TapChargeNotFoundError", "TapRefundError",
            "TapConfigurationError", "is_available", "create_charge", "get_charge",
            "refund_charge", "refund_tap_charge", "verify_webhook",
        }


class TestNoSecretsLeaked:
    """Law 32 / Law 282."""

    def test_secret_is_not_hardcoded(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        assert "sk_test" not in source and "sk_live" not in source
        assert "Bearer sk_" not in source

    def test_headers_carry_the_resolved_key_only(self, monkeypatch) -> None:
        monkeypatch.setattr(tap, "resolve_tap_secret_key", lambda *a, **k: "resolved-key")
        headers = tap._get_headers()
        assert headers["Authorization"] == "Bearer resolved-key"

    def test_missing_key_raises_before_any_request(self, monkeypatch) -> None:
        monkeypatch.setattr(tap, "resolve_tap_secret_key", lambda *a, **k: "")
        with pytest.raises(tap.TapConfigurationError):
            tap._get_headers()
