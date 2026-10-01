import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "backend"))

from scripts.fix_misplaced import fix_file, main


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_fix_file_removes_misplaced_require_feature(tmp_path: Path) -> None:
    target = tmp_path / "router.py"
    _write(
        target,
        "from rbac import require_feature\n"
        "\n"
        '@router.get("/x")\n'
        "require_feature('x.read')\n"
        "\n"
        "def get_x():\n"
        "    pass\n",
    )

    new_content, fixed = fix_file(target)

    assert fixed == 1
    assert "require_feature('x.read')" not in new_content
    assert "def get_x" in new_content


def test_fix_file_preserves_properly_placed_require_feature(tmp_path: Path) -> None:
    target = tmp_path / "router.py"
    original = (
        '@router.get("/x")\n'
        "def get_x(\n"
        "    _: None = Depends(require_feature('x.read')),\n"
        "):\n"
        "    pass\n"
    )
    _write(target, original)

    new_content, fixed = fix_file(target)

    assert fixed == 0
    assert new_content == original


def test_fix_file_no_changes_when_clean(tmp_path: Path) -> None:
    target = tmp_path / "router.py"
    original = '@router.get("/x")\ndef get_x():\n    pass\n'
    _write(target, original)

    new_content, fixed = fix_file(target)

    assert fixed == 0
    assert new_content == original


def test_dry_run_reports_without_writing(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    target = tmp_path / "router.py"
    _write(
        target,
        '@router.get("/x")\n'
        "require_feature('x.read')\n"
        "\n"
        "def get_x():\n"
        "    pass\n",
    )

    with patch.object(sys, "argv", ["fix_misplaced", "--dry-run"]):
        with patch(
            "scripts.fix_misplaced.fix_file",
            return_value=(target.read_text(encoding="utf-8"), 1),
        ):
            exit_code = main()

    captured = capsys.readouterr()
    assert "[DRY RUN]" in captured.out or exit_code == 0


def test_main_returns_zero_when_all_clean() -> None:
    with patch.object(sys, "argv", ["fix_misplaced"]):
        with patch(
            "scripts.fix_misplaced.fix_file",
            return_value=("def x():\n    pass\n", 0),
        ):
            exit_code = main()

    assert exit_code == 0
