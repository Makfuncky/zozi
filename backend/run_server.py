#!/usr/bin/env python3
"""Simple wrapper that starts uvicorn on the configured port."""
import logging
import os
import sys
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger("run_server")

if __name__ == "__main__":
    host = "127.0.0.1"
    port = int(os.environ.get("BACKEND_PORT", 8000))

    try:
        logger.info("=== Starting uvicorn on %s:%d ===", host, port)
        import uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            log_level="info",
            reload=False,
            workers=1,
        )
        logger.info("=== uvicorn.run() returned (server stopped) ===")
    except SystemExit as e:
        logger.error("!!! SystemExit(%s) !!!", e.code)
    except BaseException:
        logger.error("!!! UNCAUGHT EXCEPTION !!!\n%s", traceback.format_exc())
        sys.exit(1)
    else:
        logger.info("=== Server exited cleanly ===")

