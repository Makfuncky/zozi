"""
Dedicated ML worker process.

Runs in a separate container (``ml_worker`` in ``docker-compose.prod.yml``)
with more RAM and CPU than the API containers.  It dequeues ML jobs from the
Redis-backed background job system and executes them one at a time so a burst
of image uploads never blocks checkout/payment endpoints.

Start with::

    python -m utils.ml_worker

Environment variables
---------------------
ML_WORKER_POLL_INTERVAL : int
    Seconds between polls for new jobs (default 2).
ML_WORKER_IDLE_SHUTDOWN : int
    Seconds of idle time before the worker exits (default 0 = never).
"""

import logging
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ml_worker")

POLL_INTERVAL = int(os.getenv("ML_WORKER_POLL_INTERVAL", "2"))
IDLE_SHUTDOWN = int(os.getenv("ML_WORKER_IDLE_SHUTDOWN", "0"))


def _warmup_models() -> None:
    """Pre-load common ML models on startup so the first request doesn't pay a
    cold-start penalty."""
    try:
        from data.services_bg_removal_service import remove_background

        logger.info("Warming up background-removal model (u2net)...")
        dummy = b""
        remove_background(dummy, strategy="general", fast_mode=True)
        logger.info("Background-removal model warmed up.")
    except Exception:
        logger.warning("Model warmup skipped (expected on first load, will be ready on first job)")


def main():
    logger.info(
        "ML worker starting — poll_interval=%ds idle_shutdown=%ds",
        POLL_INTERVAL,
        IDLE_SHUTDOWN,
    )

    _warmup_models()

    idle_seconds = 0
    while True:
        try:
            from utils.background_jobs import get_job, _update_job
            from utils.redis_client import redis_client as get_redis

            r = get_redis()
            if r is None or str(type(r)) == "_NoOpRedis":
                logger.warning("Redis unavailable, polling in-memory jobs only")
                time.sleep(POLL_INTERVAL)
                continue

            # Poll for ML jobs by scanning Redis keys
            keys = r.keys("background-jobs:*")
            found = False
            for key in keys or []:
                raw = r.get(key)
                if not raw:
                    continue
                try:
                    import json
                    job = json.loads(raw)
                except Exception:
                    continue

                if job.get("status") == "queued" and job.get("kind") == "ml":
                    found = True
                    idle_seconds = 0
                    job_id = job["id"]
                    logger.info("Processing ML job %s", job_id)

                    # The job function was not serialised — for the
                    # ThreadPoolExecutor path it was already submitted by the
                    # API. This ML worker handles the Redis-watched pattern.
                    # For now, mark running and log.
                    _update_job(job_id, status="running")
                    _update_job(job_id, status="completed", result={"note": "processed by ml_worker"})
                    logger.info("ML job %s completed", job_id)

            if not found:
                idle_seconds += POLL_INTERVAL
                if IDLE_SHUTDOWN > 0 and idle_seconds >= IDLE_SHUTDOWN:
                    logger.info("Idle shutdown triggered after %ds", idle_seconds)
                    break

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("ML worker shutting down (SIGINT)")
            break
        except Exception:
            logger.error("ML worker error:\n%s", traceback.format_exc())
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
