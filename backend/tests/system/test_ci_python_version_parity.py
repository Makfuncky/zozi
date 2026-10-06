"""CI/deploy interpreter parity gate (FILE-99 / TEST-017).

The backend runtime interpreter is declared in exactly one machine-readable
place: ``backend/pyproject.toml`` -> ``requires-python = ">=3.13,<3.14"``
(mirrored by ``backend/Dockerfile`` / ``backend/Dockerfile.prod`` ->
``FROM python:3.13-slim``, and by ``TECHNOLOGY_STACK.md`` section 1, which pins
the 3.13 line and forbids silent drift).

Every GitHub Actions job that installs Python must resolve to that same
interpreter. If a workflow pins its own literal, the pre-deploy gate can pass on
an interpreter that neither CI approved nor the deployed image will run -- which
defeats the gate (ARCHITECTURE_STACK.md Law 71) and makes the deploy verdict
non-reproducible.

This module owns ``.github/workflows/deploy.yml`` (the pre-deploy validation job
that gates the Railway/Vercel staging and production deploys). Other workflows
are owned by their own resolution blocks and are deliberately NOT swept here.

Scope of this file (contract FILE-99):
  * deploy.yml  -> must resolve to the canonical minor.
  * ci.yml      -> read as the reference the deploy gate is compared against.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
import yaml

from tests._support import laws

# tests/_support/laws.py sets BACKEND_ROOT to backend/tests (two levels up from
# that file), so derive the real roots explicitly instead of trusting the name.
# A layout change must fail loudly (see TestRepoLayoutIsAsExpected) rather than
# silently resolve paths against the wrong directory.
_TESTS_ROOT: Path = Path(__file__).resolve().parent.parent
BACKEND_ROOT: Path = _TESTS_ROOT.parent
REPO_ROOT: Path = BACKEND_ROOT.parent
WORKFLOWS_DIR: Path = REPO_ROOT / ".github" / "workflows"
PYPROJECT: Path = BACKEND_ROOT / "pyproject.toml"
LAWS_HELPER_ROOT: Path = laws.BACKEND_ROOT

# The workflow this block owns, and the workflow it must agree with.
DEPLOY_WORKFLOW: Path = WORKFLOWS_DIR / "deploy.yml"
CI_WORKFLOW: Path = WORKFLOWS_DIR / "ci.yml"

# Workflows owned by other resolution blocks -- read for reference only, never
# asserted on here (a repo-wide sweep would be red for files outside §1).
NOT_OWNED: tuple[Path, ...] = (
    WORKFLOWS_DIR / "schema-audit.yml",
    WORKFLOWS_DIR / "router-generation.yml",
)

_PY_VERSION_LITERAL = re.compile(r"^\d+\.\d+(?:\.\d+)?$")
_ENV_REF = re.compile(r"^\$\{\{\s*env\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}$")


def same_minor(version: str, minor: str) -> bool:
    """True when ``version`` names the ``major.minor`` line ``minor``.

    ``actions/setup-python`` accepts a floating minor ("3.13") or a full patch
    ("3.13.5"); both satisfy a pin on the 3.13 line.
    """
    return version == minor or version.startswith(f"{minor}.")


def drifted_python_minor() -> str:
    """A minor guaranteed to differ from canonical, for the error-path probes.

    Derived, not hard-coded, so the error-path tests keep testing drift after
    the supported interpreter line moves.
    """
    major, minor = canonical_python_minor().split(".")
    return f"{major}.{int(minor) + 1}"


class VersionResolutionError(RuntimeError):
    """A setup-python step declares a version this resolver cannot resolve."""


def canonical_python_minor() -> str:
    """Return the minor version of the interpreter the backend supports.

    Derived from ``backend/pyproject.toml`` -> ``requires-python``, which is the
    single machine-readable declaration of the supported interpreter line. Not
    hard-coded: bump the range and every gate below follows it.
    """
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8-sig"))
    project = data.get("project")
    if not isinstance(project, dict):
        pytest.fail("backend/pyproject.toml has no [project] table")
    spec = project.get("requires-python")
    if not isinstance(spec, str) or not spec:
        pytest.fail("backend/pyproject.toml [project] is missing requires-python")
    match = re.search(r">=\s*(\d+)\.(\d+)", spec)
    if match is None:
        pytest.fail(
            f"requires-python={spec!r} does not pin a lower bound like '>=3.13,<3.14'"
        )
    return f"{match.group(1)}.{match.group(2)}"


def _env_for_job(workflow: dict, job: dict) -> dict:
    """Merge the env a step can read: workflow scope, then job scope."""
    merged: dict = {}
    workflow_env = workflow.get("env")
    if isinstance(workflow_env, dict):
        merged.update(workflow_env)
    job_env = job.get("env")
    if isinstance(job_env, dict):
        merged.update(job_env)
    return merged


def _resolve_step_version(raw: object, env: dict, where: str) -> str:
    """Resolve one ``python-version`` value against the env visible to it."""
    if isinstance(raw, (int, float)):
        # YAML turns a bare 3.13 into a float; Actions would stringify it, but a
        # bare (unquoted) version is fragile, so reject it explicitly.
        raise VersionResolutionError(
            f"{where}: python-version must be quoted, got the bare number {raw!r}"
        )
    if not isinstance(raw, str) or not raw.strip():
        raise VersionResolutionError(
            f"{where}: python-version is missing or empty ({raw!r})"
        )
    value = raw.strip()
    if _PY_VERSION_LITERAL.match(value):
        return value
    match = _ENV_REF.match(value)
    if match is None:
        raise VersionResolutionError(
            f"{where}: python-version {value!r} is neither a version literal "
            "nor a '${{ env.<NAME> }}' reference"
        )
    name = match.group(1)
    if name not in env:
        raise VersionResolutionError(
            f"{where}: python-version references env.{name} which is not "
            f"defined in this workflow or job (visible env keys: {sorted(env)})"
        )
    resolved = env[name]
    if not isinstance(resolved, str) or not _PY_VERSION_LITERAL.match(resolved.strip()):
        raise VersionResolutionError(
            f"{where}: env.{name} resolves to {resolved!r}, which is not a "
            "version literal"
        )
    return resolved.strip()


def resolve_workflow_python_versions(workflow_path: Path) -> list[str]:
    """Return every Python version the workflow's setup-python steps resolve to.

    Raises VersionResolutionError for any step whose version cannot be resolved;
    never guesses and never skips a step.
    """
    raw_text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(raw_text)
    if not isinstance(workflow, dict):
        raise VersionResolutionError(f"{workflow_path.name}: not a YAML mapping")
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        raise VersionResolutionError(f"{workflow_path.name}: no jobs declared")

    resolved: list[str] = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            raise VersionResolutionError(
                f"{workflow_path.name}: job {job_name!r} is not a mapping"
            )
        env = _env_for_job(workflow, job)
        for index, step in enumerate(job.get("steps") or []):
            if not isinstance(step, dict):
                raise VersionResolutionError(
                    f"{workflow_path.name}: job {job_name!r} step {index} "
                    "is not a mapping"
                )
            uses = str(step.get("uses") or "")
            if not uses.startswith("actions/setup-python"):
                continue
            with_block = step.get("with")
            if not isinstance(with_block, dict) or "python-version" not in with_block:
                raise VersionResolutionError(
                    f"{workflow_path.name}: job {job_name!r} step {index} uses "
                    f"{uses} but declares no python-version"
                )
            resolved.append(
                _resolve_step_version(
                    with_block["python-version"],
                    env,
                    where=f"{workflow_path.name}:job {job_name}:step {index}",
                )
            )
    if not resolved:
        raise VersionResolutionError(
            f"{workflow_path.name}: declares no actions/setup-python step"
        )
    return resolved


def find_python_version_violations(workflow_path: Path) -> list[str]:
    """Return every way the workflow's interpreter fails the canonical pin.

    Empty list == the workflow is compliant. Resolution failures are returned as
    violations rather than raised, so one run reports every problem at once.
    """
    try:
        versions = resolve_workflow_python_versions(workflow_path)
    except VersionResolutionError as exc:
        return [str(exc)]
    canonical = canonical_python_minor()
    return [
        f"{workflow_path.name} installs Python {got}, expected the canonical "
        f"{canonical} (backend/pyproject.toml requires-python)"
        for got in versions
        if not same_minor(got, canonical)
    ]


class TestRepoLayoutIsAsExpected:
    """The path derivation above must stay anchored to the real tree."""

    def test_roots_are_anchored(self):
        assert (REPO_ROOT / ".github" / "workflows").is_dir(), (
            f"workflow dir not found under {REPO_ROOT}; repo layout changed"
        )
        assert PYPROJECT.is_file(), f"missing {PYPROJECT}"
        assert BACKEND_ROOT.name == "backend", (
            f"expected the backend package at {BACKEND_ROOT}"
        )

    def test_laws_helper_root_agrees(self):
        assert LAWS_HELPER_ROOT == BACKEND_ROOT, (
            f"tests._support.laws.BACKEND_ROOT is {LAWS_HELPER_ROOT}, "
            f"expected {BACKEND_ROOT}"
        )


class TestDeployWorkflowPythonVersionParity:
    """REGRESSION (outcome): the pre-deploy gate runs the interpreter CI runs."""

    def test_deploy_workflow_has_python_gate(self):
        assert DEPLOY_WORKFLOW.exists(), (
            f"missing {DEPLOY_WORKFLOW} -- the deploy pipeline is undefined"
        )
        versions = resolve_workflow_python_versions(DEPLOY_WORKFLOW)
        assert versions, "deploy.yml installs no Python; the pre-deploy gate is gone"

    def test_deploy_workflow_uses_canonical_python(self):
        """TEST-017: deploy.yml pinned 3.11 while ci.yml ran 3.13."""
        violations = find_python_version_violations(DEPLOY_WORKFLOW)
        assert not violations, (
            "deploy.yml Python version drift:\n  " + "\n  ".join(violations)
        )

    def test_deploy_workflow_matches_ci_workflow(self):
        """The deploy gate and the CI gate must be the same interpreter."""
        deploy_versions = set(resolve_workflow_python_versions(DEPLOY_WORKFLOW))
        ci_versions = set(resolve_workflow_python_versions(CI_WORKFLOW))
        assert deploy_versions == ci_versions, (
            f"deploy.yml resolves to {sorted(deploy_versions)} but ci.yml "
            f"resolves to {sorted(ci_versions)}; the pre-deploy gate must run "
            "the interpreter CI approved"
        )

    def test_deploy_workflow_matches_runtime_image(self):
        """The gate must also match the interpreter the image actually runs."""
        image_lines = [
            line.strip()
            for line in (BACKEND_ROOT / "Dockerfile.prod")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip().startswith("FROM python:")
        ]
        assert image_lines, "backend/Dockerfile.prod has no FROM python: line"
        image_minor = image_lines[0].removeprefix("FROM python:").split("-")[0]
        assert image_minor == canonical_python_minor(), (
            f"backend/Dockerfile.prod runs Python {image_minor} but "
            f"pyproject declares {canonical_python_minor()}"
        )
        for version in resolve_workflow_python_versions(DEPLOY_WORKFLOW):
            assert same_minor(version, image_minor), (
                f"deploy.yml installs {version}; the deployed image runs "
                f"{image_minor}"
            )


class TestVersionResolverErrorPaths:
    """ERROR PATH: the guard must report drift, not pass vacuously."""

    @pytest.fixture
    def tmp_workflow_dir(self, tmp_path):
        """A workflow dir carrying the two reference workflows, plus one slot."""
        target = tmp_path / "drift-probe.yml"
        target.write_text("name: probe\njobs: {}\n", encoding="utf-8")
        return target

    def test_drifted_literal_is_reported(self, tmp_workflow_dir):
        drifted = drifted_python_minor()
        tmp_workflow_dir.write_text(
            "name: probe\n"
            f"env:\n"
            f"  PYTHON_VERSION: \"{canonical_python_minor()}\"\n"
            "jobs:\n"
            "  gate:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/setup-python@v5\n"
            "        with:\n"
            f"          python-version: \"{drifted}\"\n",
            encoding="utf-8",
        )
        violations = find_python_version_violations(tmp_workflow_dir)
        assert len(violations) == 1, violations
        assert drifted in violations[0], violations[0]
        assert canonical_python_minor() in violations[0], violations[0]

    def test_unresolvable_env_reference_is_reported(self, tmp_workflow_dir):
        tmp_workflow_dir.write_text(
            "name: probe\n"
            "jobs:\n"
            "  gate:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/setup-python@v5\n"
            "        with:\n"
            "          python-version: ${{ env.MISSING_PYTHON_VERSION }}\n",
            encoding="utf-8",
        )
        violations = find_python_version_violations(tmp_workflow_dir)
        assert len(violations) == 1, violations
        assert "MISSING_PYTHON_VERSION" in violations[0], violations[0]

    def test_canonical_env_reference_resolves_clean(self, tmp_workflow_dir):
        """The fix's own shape must be green -- no false positive."""
        tmp_workflow_dir.write_text(
            "name: probe\n"
            f"env:\n"
            f"  PYTHON_VERSION: \"{canonical_python_minor()}\"\n"
            "jobs:\n"
            "  gate:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/setup-python@v5\n"
            "        with:\n"
            "          python-version: ${{ env.PYTHON_VERSION }}\n",
            encoding="utf-8",
        )
        assert find_python_version_violations(tmp_workflow_dir) == []

    def test_setup_python_without_version_is_reported(self, tmp_workflow_dir):
        tmp_workflow_dir.write_text(
            "name: probe\n"
            "jobs:\n"
            "  gate:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/setup-python@v5\n"
            "        with:\n"
            "          cache: pip\n",
            encoding="utf-8",
        )
        violations = find_python_version_violations(tmp_workflow_dir)
        assert len(violations) == 1, violations
        assert "no python-version" in violations[0], violations[0]

    def test_workflow_without_python_step_is_reported(self, tmp_workflow_dir):
        tmp_workflow_dir.write_text(
            "name: probe\n"
            "jobs:\n"
            "  gate:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n",
            encoding="utf-8",
        )
        violations = find_python_version_violations(tmp_workflow_dir)
        assert len(violations) == 1, violations
        assert "no actions/setup-python step" in violations[0], violations[0]

    def test_unquoted_bare_number_is_reported(self, tmp_workflow_dir):
        """A bare 3.13 is a float in YAML; it must not be silently accepted."""
        tmp_workflow_dir.write_text(
            "name: probe\n"
            "jobs:\n"
            "  gate:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/setup-python@v5\n"
            "        with:\n"
            f"          python-version: {canonical_python_minor()}\n",
            encoding="utf-8",
        )
        violations = find_python_version_violations(tmp_workflow_dir)
        assert len(violations) == 1, violations
        assert "quoted" in violations[0], violations[0]

    def test_job_scope_env_overrides_workflow_scope(self, tmp_workflow_dir):
        """A job may legitimately pin its own value; resolution must follow it."""
        drifted = drifted_python_minor()
        tmp_workflow_dir.write_text(
            "name: probe\n"
            f"env:\n"
            f"  PYTHON_VERSION: \"{canonical_python_minor()}\"\n"
            "jobs:\n"
            "  gate:\n"
            "    runs-on: ubuntu-latest\n"
            "    env:\n"
            f"      PYTHON_VERSION: \"{drifted}\"\n"
            "    steps:\n"
            "      - uses: actions/setup-python@v5\n"
            "        with:\n"
            "          python-version: ${{ env.PYTHON_VERSION }}\n",
            encoding="utf-8",
        )
        violations = find_python_version_violations(tmp_workflow_dir)
        assert len(violations) == 1, violations
        assert drifted in violations[0], violations[0]


class TestNotOwnedWorkflowsAreNotSwept:
    """Guard against a regression test that fails for files outside §1."""

    @pytest.mark.parametrize("workflow_path", NOT_OWNED, ids=lambda p: p.name)
    def test_untouched_workflow_still_parses(self, workflow_path):
        """schema-audit.yml / router-generation.yml have their own blocks.

        They may still drift from canonical; this block must not claim them.
        Asserting only that they parse keeps this file from becoming red for
        a finding it does not own.
        """
        assert workflow_path.exists(), f"missing {workflow_path}"
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        assert isinstance(workflow, dict)
        assert workflow.get("jobs"), f"{workflow_path.name} declares no jobs"
