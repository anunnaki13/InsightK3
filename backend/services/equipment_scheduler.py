import asyncio
import logging
import os
from datetime import datetime, time, timedelta, timezone

from services.alert_service import run_daily_alert_check


logger = logging.getLogger(__name__)


def _get_alert_check_hour() -> int:
    raw_value = os.environ.get("ALERT_CHECK_HOUR", "6")
    try:
        hour = int(raw_value)
    except ValueError:
        logger.warning("Invalid ALERT_CHECK_HOUR=%s, falling back to 6", raw_value)
        return 6

    if 0 <= hour <= 23:
        return hour

    logger.warning("Out-of-range ALERT_CHECK_HOUR=%s, falling back to 6", raw_value)
    return 6


def _seconds_until_next_run(target_hour: int) -> float:
    now = datetime.now(timezone.utc)
    target = datetime.combine(now.date(), time(hour=target_hour, tzinfo=timezone.utc))
    if target <= now:
        target = target + timedelta(days=1)
    return max((target - now).total_seconds(), 1.0)


async def equipment_alert_scheduler(db) -> None:
    target_hour = _get_alert_check_hour()
    logger.info("Starting equipment alert scheduler with daily run at %02d:00 UTC", target_hour)

    try:
        await run_daily_alert_check(db)
        logger.info("Initial equipment alert sync completed")
    except Exception:
        logger.exception("Initial equipment alert sync failed")

    while True:
        sleep_seconds = _seconds_until_next_run(target_hour)
        logger.info("Next equipment alert run scheduled in %.0f seconds", sleep_seconds)
        await asyncio.sleep(sleep_seconds)
        try:
            await run_daily_alert_check(db)
            logger.info("Scheduled equipment alert sync completed")
        except Exception:
            logger.exception("Scheduled equipment alert sync failed")
