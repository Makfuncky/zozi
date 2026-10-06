import ast
import os

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENV_PY = os.path.join(_BACKEND_ROOT, "alembic", "env.py")


def _source() -> str:
    with open(_ENV_PY, "r", encoding="utf-8") as f:
        return f.read()


def test_env_py_uses_async_engine():
    src = _source()
    assert "create_async_engine" in src, "run_migrations_online must use create_async_engine"
    assert "NullPool" in src, "run_migrations_online must use NullPool"
    assert "run_sync" in src, (
        "run_migrations_online must use connection.run_sync to bridge async to sync context"
    )


def test_env_py_does_not_rewrite_asyncpg_to_sync():
    src = _source()
    # After rewriting asyncpg->postgresql://, the original asyncpg scheme must not appear
    # in a way that would force a sync driver.
    assert "replace(\"postgresql+asyncpg://\", \"postgresql://\"" not in src, (
        "env.py must not rewrite asyncpg DSN to sync postgresql://"
    )


def test_env_py_offline_mode_still_works():
    src = _source()
    tree = ast.parse(src)
    funcs = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert "run_migrations_offline" in funcs, "run_migrations_offline must still exist"
    offline_start = funcs["run_migrations_offline"].lineno
    # Find the next function def after offline
    next_lines = [
        node.lineno for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.lineno > offline_start
    ]
    offline_end = min(next_lines) if next_lines else len(src.splitlines())
    offline_src = "\n".join(src.splitlines()[offline_start - 1 : offline_end - 1])
    assert "context.configure" in offline_src
    assert "literal_binds=True" in offline_src


def test_env_py_no_psycopg2_dependency():
    src = _source()
    assert "psycopg2" not in src, "env.py must not reference psycopg2"


def test_env_py_preserves_url_handling():
    src = _source()
    assert "DATABASE_URL_DIRECT" in src, "env.py must still honour DATABASE_URL_DIRECT"
    assert "DATABASE_URL" in src, "env.py must still honour DATABASE_URL fallback"
