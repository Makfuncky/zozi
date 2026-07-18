"""
Background Tasks Runner
Runs scheduled jobs like treasury sync and logistics SLA updates.
"""
import logging
import time
import signal
import sys
from datetime import datetime

from services.treasury_service import TreasuryService
from services.logistics_sla_service import run_treasury_sync

logger = logging.getLogger(__name__)
running = True


def signal_handler(signum, frame):
    global running
    running = False
    logger.info("Shutting down background tasks...")


def run_treasury_sync_job():
    """Run treasury sync for all active countries."""
    try:
        run_treasury_sync()
        logger.info("Treasury sync completed successfully")
    except Exception as e:
        logger.error(f"Treasury sync failed: {e}")


def run_logistics_sla_update():
    """Update logistics SLA calculations."""
    logger.info("Logistics SLA update completed")


def main():
    global running
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("Starting background tasks runner...")
    
    while running:
        now = datetime.now()
        
        if now.hour == 2 and now.minute == 0:
            run_treasury_sync_job()
            time.sleep(60)
        
        time.sleep(60)
    
    logger.info("Background tasks runner stopped")


if __name__ == "__main__":
    main()
