import argparse
import importlib.util
import logging
from pathlib import Path
import sys

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
MAIN_PATH = BACKEND_ROOT / "main.py"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
MODULE_SPEC = importlib.util.spec_from_file_location("zozi_backend_main", MAIN_PATH)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise RuntimeError(f"Unable to load backend app module from {MAIN_PATH}")
main = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(main)


def run_smoke(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    health_summary = ""

    logger = logging.getLogger()
    file_handler = logging.FileHandler(output_path, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(file_handler)

    try:
        with TestClient(main.app) as client:
            response = client.get("/health")
            health_summary = f"health_response={response.status_code} body={response.text}\n"
    finally:
        logger.removeHandler(file_handler)
        file_handler.close()

    if health_summary:
        with output_path.open("a", encoding="utf-8") as stream:
            stream.write(health_summary)

    return output_path


def main_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Boot the backend once and write startup health and scheduler lifecycle logs to an artifact file.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/backend-startup-smoke.log",
        help="Path to the artifact log file.",
    )
    args = parser.parse_args()
    artifact = run_smoke(Path(args.output))
    print(artifact)


if __name__ == "__main__":
    main_cli()