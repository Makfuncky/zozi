import sys
import traceback

import uvicorn

import main


def run() -> int:
    print("uvicorn-probe-start")
    try:
        uvicorn.run(main.app, host="127.0.0.1", port=8001, log_level="debug")
    except BaseException as exc:
        print(f"uvicorn-probe-raised={type(exc).__name__}: {exc}")
        traceback.print_exc()
        return 99

    print("uvicorn-probe-returned")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
