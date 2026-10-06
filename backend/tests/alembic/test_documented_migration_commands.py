"""Law 217/219 gate: the *documented* migration commands must actually work.

R-02 (RUNTIME_PROBLEM.md): `npm run db:migrate` ran `alembic upgrade head` from
``backend/`` while the config file lives at ``backend/alembic/alembic.ini``, so
the documented one-command path failed with ``No 'script_location' key found``.
The CI/CD workflows had the same defect.

These assertions keep every documented entry point pointed at a config file that
exists, so a future file move cannot silently break deploy/rollback again.
"""
from __future__ import annotations

import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_REPO_ROOT = os.path.dirname(_BACKEND_ROOT)
_ALEMBIC_INI = os.path.join(_BACKEND_ROOT, "alembic", "alembic.ini")


def test_alembic_ini_exists_where_the_documented_command_expects_it():
    assert os.path.isfile(_ALEMBIC_INI), (
        "backend/alembic/alembic.ini is the config every documented migration "
        "command must target (npm run db:migrate, deploy.yml, rollback.yml)."
    )


def test_package_json_db_migrate_targets_the_config_file():
    with open(os.path.join(_REPO_ROOT, "package.json"), encoding="utf-8") as fh:
        scripts = json.load(fh)["scripts"]
    migrate = scripts.get("db:migrate", "")
    assert "alembic" in migrate, "db:migrate must invoke alembic"
    assert "-c alembic/alembic.ini" in migrate, (
        "npm run db:migrate must pass -c alembic/alembic.ini — bare "
        f"`alembic upgrade head` fails from backend/. Got: {migrate}"
    )


def test_ci_workflows_pass_the_alembic_config_file():
    pattern = re.compile(r"alembic\s+upgrade\s+head")
    offenders = []
    for name in ("deploy.yml", "rollback.yml", "ci.yml"):
        path = os.path.join(_REPO_ROOT, ".github", "workflows", name)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                if pattern.search(line) and "-c " not in line:
                    offenders.append(f"{name}:{lineno}: {line.strip()}")
    assert not offenders, (
        "CI migration steps must use `alembic -c <ini> upgrade head` "
        "(the config file is not on the default lookup path):\n" + "\n".join(offenders)
    )
