from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / "backend" / "providers" / "ai" / "image_ai_service.py"
FORBIDDEN = ("HF_API_TOKEN", "BG_REMOVAL_MODEL", "MULTIVIEW_SPACE_ID", "ZERO123_MODEL")


def test_no_raw_os_getenv_for_provider_config():
    source = TARGET.read_text(encoding="utf-8")
    lines = source.splitlines()
    offenders = []
    for i, line in enumerate(lines, 1):
        if "os.getenv(" in line:
            offenders.append(f"  line {i}: {line.strip()}")
    assert not offenders, (
        "Raw os.getenv found for provider config values in "
        f"{TARGET}:\n" + "\n".join(offenders)
    )
