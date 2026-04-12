"""Client for querying Home Assistant long-term statistics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

from homeassistant.components.recorder.statistics import (
    statistics_during_period,
)
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def get_period_average(
    hass: HomeAssistant,
    entity_id: str,
    start: datetime,
    end: datetime,
) -> float | None:
    """Get the mean temperature over a date range using long-term statistics."""
    stats = await hass.async_add_executor_job(
        _get_statistics, hass, entity_id, start, end, "day"
    )
    if not stats:
        return None

    means = [s["mean"] for s in stats if s.get("mean") is not None]
    if not means:
        return None
    return sum(means) / len(means)


async def get_daily_means(
    hass: HomeAssistant,
    entity_id: str,
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Get daily mean values for sparkline rendering."""
    stats = await hass.async_add_executor_job(
        _get_statistics, hass, entity_id, start, end, "day"
    )
    if not stats:
        return []

    return [
        {
            "date": s["start"].isoformat() if isinstance(s["start"], datetime) else s["start"],
            "mean": round(s["mean"], 2) if s.get("mean") is not None else None,
        }
        for s in stats
        if s.get("mean") is not None
    ]


async def get_last_year_average(
    hass: HomeAssistant,
    entity_id: str,
    days: int,
) -> tuple[float | None, datetime, datetime]:
    """Get the average for the same period one year ago.

    Returns (average, period_start, period_end).
    """
    now = datetime.now(timezone.utc)
    end = now - timedelta(days=365)
    start = end - timedelta(days=days)
    avg = await get_period_average(hass, entity_id, start, end)
    return avg, start, end


def _get_statistics(
    hass: HomeAssistant,
    entity_id: str,
    start: datetime,
    end: datetime,
    period: str,
) -> list[dict]:
    """Fetch statistics from the recorder (runs in executor)."""
    try:
        result = statistics_during_period(
            hass,
            start_time=start,
            end_time=end,
            statistic_ids={entity_id},
            period=period,
            units=None,
            types={"mean"},
        )
        return result.get(entity_id, [])
    except Exception:
        _LOGGER.debug("Failed to fetch statistics for %s", entity_id, exc_info=True)
        return []
