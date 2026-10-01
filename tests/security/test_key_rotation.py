from pathlib import Path


def test_periodic_key_rotation_task_exists():
    target = Path(__file__).resolve().parent.parent.parent / "backend" / "jobs" / "periodic_tasks.py"
    content = target.read_text()
    assert "def check_key_rotation" in content
    assert "tasks.periodic_tasks.check_key_rotation" in content
