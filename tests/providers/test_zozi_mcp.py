from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / "backend" / "providers" / "ai" / "zozi_mcp.py"
FORBIDDEN_PREFIXES = ("ZOZI_MCP_API_URL", "ZOZI_MCP_USERNAME", "ZOZI_MCP_PASSWORD")


def test_no_raw_os_getenv_for_mcp_config():
    source = TARGET.read_text(encoding="utf-8")
    lines = source.splitlines()
    offenders = []
    for i, line in enumerate(lines, 1):
        if "os.getenv(" in line:
            upper = line.upper()
            if any(prefix in upper for prefix in FORBIDDEN_PREFIXES):
                offenders.append(f"  line {i}: {line.strip()}")
    assert not offenders, (
        "Raw os.getenv found for ZOZI_MCP_* config values in "
        f"{TARGET}:\n" + "\n".join(offenders)
    )
