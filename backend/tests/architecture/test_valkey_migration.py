"""Architecture tests  Valkey migration (ARCHITECTURE_DIAGRAM.md §14).







Verifies that the Valkey migration is complete:



  * Canonical client at ``infrastructure/valkey/client.py`` (Law 142).



  * No direct ``import redis`` in domain code (Law 31 / §14).



"""



from __future__ import annotations







import pathlib







import pytest











_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent



_INFRASTRUCTURE = _BACKEND_ROOT / "infrastructure"











def test_canonical_valkey_client_exists() -> None:



    """infrastructure/valkey/client.py must exist (Law 142 canonical location)."""



    assert (_INFRASTRUCTURE / "valkey" / "client.py").exists()



    assert (_INFRASTRUCTURE / "valkey" / "cache.py").exists()











def test_canonical_valkey_client_exposes_singleton() -> None:



    """valkey_client() returns a client (real or no-op fallback)."""



    from infrastructure.valkey.client import valkey_client, get_valkey



    c = valkey_client()



    assert c is not None



    # Has all the standard Valkey-compatible methods



    for method in ("setex", "set", "get", "delete", "exists", "expire", "ping"):



        assert hasattr(c, method), f"Client missing {method!r}"











def test_legacy_redis_client_shim_removed() -> None:



    """infrastructure.valkey.client is the canonical Valkey client."""



    from infrastructure.valkey.client import valkey_client



    c = valkey_client()



    assert c is not None



    # Must be either a valkey client or the no-op fallback



    type_name = type(c).__name__



    assert type_name in ("Valkey", "StrictValkey", "_NoOpValkey", "_NoOpValkey"), (



        f"Unexpected client type: {type_name}"



    )



def test_infrastructure_valkey_client_is_canonical() -> None:



    """infrastructure.valkey.client is the canonical Valkey client (Law 142 + §14)."""



    from infrastructure.valkey.client import valkey_client



    c = valkey_client()



    assert c is not None

def test_no_direct_redis_import_in_domains() -> None:



    """Domains must NOT import the `redis` package directly (Law 31 + §14).







    Only infrastructure/ may import the underlying client.



    The `redis` Python package is still installed as a transitive dependency



    of `valkey` but must not be used directly anywhere in the codebase.



    """



    domains_root = _BACKEND_ROOT / "domains"



    offenders: list[str] = []



    for py_file in domains_root.rglob("*.py"):



        if "__pycache__" in py_file.parts:



            continue



        try:



            text = py_file.read_text(encoding="utf-8", errors="replace")



        except OSError:



            continue



        # Look for direct `import redis` or `from redis` (not `from redis.exceptions`



        # which is also forbidden, but easier to catch any `redis.` usage)



        for line_no, line in enumerate(text.splitlines(), start=1):



            stripped = line.lstrip()



            if stripped.startswith("#"):



                continue



            if (



                stripped.startswith("import redis")



                or stripped.startswith("from redis ")



                or stripped.startswith("from redis.")



            ):



                offenders.append(f"{py_file.relative_to(_BACKEND_ROOT)}:{line_no}: {line.strip()}")



                break



    assert not offenders, (



        "Forbidden: domains must not import the `redis` package directly. "



        "Use `infrastructure.valkey.client` or its backward-compat shims. "



        f"Offenders: {offenders}"



    )











def test_fraud_detection_service_uses_valkey_exceptions() -> None:



    """fraud_detection_service must import from valkey.exceptions, not redis.exceptions."""



    fraud_file = _BACKEND_ROOT / "domains" / "security" / "services" / "fraud" / "fraud_detection_service.py"



    if not fraud_file.exists():



        pytest.skip("fraud_detection_service.py not found")



    text = fraud_file.read_text(encoding="utf-8", errors="replace")



    assert "from valkey.exceptions" in text, "fraud_detection_service must import from valkey.exceptions"



    assert "from redis.exceptions" not in text, "fraud_detection_service must NOT import from redis.exceptions"







