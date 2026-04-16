"""InfluxDB client for querying temperature statistics."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class InfluxDBClient:
    """Client for querying InfluxDB for temperature statistics."""

    def __init__(
        self,
        host: str,
        port: int,
        token: str,
        org: str,
        bucket: str,
    ) -> None:
        """Initialize the InfluxDB client."""
        self.host = host
        self.port = port
        self.token = token
        self.org = org
        self.bucket = bucket
        self.base_url = f"http://{host}:{port}/api/v1/query"

    async def get_period_average(
        self,
        entity_id: str,
        start: datetime,
        end: datetime,
    ) -> float | None:
        """Get the average value for a measurement over a time period."""
        # Extract the sensor name from entity_id (e.g., sensor.living_room_temperature -> living_room_temperature)
        measurement = entity_id.split(".", 1)[1] if "." in entity_id else entity_id

        query = f"""
SELECT MEAN("value") as mean
FROM "{measurement}"
WHERE time >= '{start.isoformat()}' AND time <= '{end.isoformat()}'
"""

        result = await self._query(query)
        if result and len(result) > 0:
            values = result[0].get("values", [])
            if values and len(values) > 0 and values[0][1] is not None:
                return float(values[0][1])
        return None

    async def get_daily_means(
        self,
        entity_id: str,
        start: datetime,
        end: datetime,
    ) -> list[dict]:
        """Get daily mean values for a measurement."""
        measurement = entity_id.split(".", 1)[1] if "." in entity_id else entity_id

        query = f"""
SELECT MEAN("value") as mean
FROM "{measurement}"
WHERE time >= '{start.isoformat()}' AND time <= '{end.isoformat()}'
GROUP BY time(1d)
"""

        result = await self._query(query)
        if not result:
            return []

        daily_means = []
        for series in result:
            for time_str, mean_val in series.get("values", []):
                if mean_val is not None:
                    daily_means.append({
                        "date": time_str,
                        "mean": round(float(mean_val), 2),
                    })
        return daily_means

    async def _query(self, query: str) -> list[dict[str, Any]] | None:
        """Execute a query against InfluxDB."""
        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        params = {
            "org": self.org,
            "db": self.bucket,
            "q": query,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [{}])[0].get("series")
                    else:
                        _LOGGER.error(
                            "InfluxDB query failed with status %d: %s",
                            response.status,
                            await response.text(),
                        )
                        return None
        except asyncio.TimeoutError:
            _LOGGER.error("InfluxDB query timed out")
            return None
        except Exception as err:
            _LOGGER.error("Error querying InfluxDB: %s", err, exc_info=True)
            return None


async def get_period_average_influxdb(
    client: InfluxDBClient,
    entity_id: str,
    start: datetime,
    end: datetime,
) -> float | None:
    """Get the mean temperature over a date range using InfluxDB."""
    return await client.get_period_average(entity_id, start, end)


async def get_daily_means_influxdb(
    client: InfluxDBClient,
    entity_id: str,
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Get daily mean values for sparkline rendering from InfluxDB."""
    return await client.get_daily_means(entity_id, start, end)


async def get_last_year_average_influxdb(
    client: InfluxDBClient,
    entity_id: str,
    days: int,
) -> tuple[float | None, datetime, datetime]:
    """Get the average for the same period one year ago from InfluxDB.

    Returns (average, period_start, period_end).
    """
    now = datetime.now(timezone.utc)
    end = now - timedelta(days=365)
    start = end - timedelta(days=days)
    avg = await get_period_average_influxdb(client, entity_id, start, end)
    return avg, start, end
