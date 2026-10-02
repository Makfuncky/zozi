"""Finance domain test package.

Exists so ``tests/finance`` is a real package: without it, pytest imports the
files here as top-level modules, which collides with same-basename test files
elsewhere (e.g. ``tests/domains/test_circuit_breaker.py``) and aborts the
whole collection run with "import file mismatch".
"""
