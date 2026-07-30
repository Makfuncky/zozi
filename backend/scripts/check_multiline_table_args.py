"""Find multi-line __table_args__ that still lack a schema dict."""
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"


def process_models():
    for py in sorted(MODELS_DIR.glob("*.py")):
        if py.name.startswith("_"):
            continue

        lines = py.read_text(encoding="utf-8").splitlines()
        in_table_args = False
        start_line = None
        depth = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "__table_args__" in line and "=" in line:
                if stripped.endswith("("):
                    in_table_args = True
                    start_line = i
                    depth = 1
                elif stripped.endswith(")"):
                    if in_table_args and depth == 0:
                        in_table_args = False
                        start_line = None
                    elif in_table_args:
                        depth -= 1
                        if depth == 0:
                            in_table_args = False
                            start_line = None
                elif in_table_args:
                    depth += line.count("(") - line.count(")")
                continue


if __name__ == "__main__":
    process_models()
