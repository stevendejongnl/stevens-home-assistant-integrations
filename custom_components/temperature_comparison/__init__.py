"""The Temperature Comparison integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.loader import async_get_integration

from .const import (
    CONF_DATA_SOURCE,
    CONF_HISTORY_DAYS,
    CONF_INSIDE_ENTITY,
    CONF_OUTSIDE_ENTITY,
    CONF_UPDATE_INTERVAL,
    CONF_WEIGHT_OUTDOOR,
    DATA_SOURCE_INFLUXDB,
    DATA_SOURCE_RECORDER,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_WEIGHT_OUTDOOR,
    DOMAIN,
)
from .influxdb_client import (
    InfluxDBClient,
    get_daily_means_influxdb,
    get_last_year_average_influxdb,
    get_period_average_influxdb,
)
from .statistics_client import (
    get_daily_means,
    get_last_year_average,
    get_period_average,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


@dataclass
class TemperatureComparisonData:
    """Data returned by the coordinator."""

    inside_current: float | None = None
    outside_current: float | None = None
    inside_avg_period: float | None = None
    outside_avg_period: float | None = None
    inside_avg_last_year: float | None = None
    outside_avg_last_year: float | None = None
    inside_last_year_start: str = ""
    inside_last_year_end: str = ""
    outside_last_year_start: str = ""
    outside_last_year_end: str = ""
    corrected_difference: float | None = None
    trend: str = "unknown"
    inside_daily_history: list[dict] = field(default_factory=list)
    outside_daily_history: list[dict] = field(default_factory=list)
    history_days: int = DEFAULT_HISTORY_DAYS
    weight_outdoor: float = DEFAULT_WEIGHT_OUTDOOR


class TemperatureComparisonCoordinator(DataUpdateCoordinator[TemperatureComparisonData]):
    """Coordinator that computes temperature comparisons from HA statistics."""

    def __init__(
        self,
        hass: HomeAssistant,
        inside_entity: str,
        outside_entity: str,
        history_days: int,
        weight_outdoor: float,
        update_interval: int,
        data_source: str = DATA_SOURCE_RECORDER,
        influxdb_client: InfluxDBClient | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self.inside_entity = inside_entity
        self.outside_entity = outside_entity
        self.history_days = history_days
        self.weight_outdoor = weight_outdoor
        self.data_source = data_source
        self.influxdb_client = influxdb_client

    async def _async_update_data(self) -> TemperatureComparisonData:
        inside_current = self._get_entity_value(self.inside_entity)
        outside_current = self._get_entity_value(self.outside_entity)

        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=self.history_days)

        inside_avg = None
        outside_avg = None
        inside_ly = None
        outside_ly = None
        in_ly_start = now - timedelta(days=365 + self.history_days)
        in_ly_end = now - timedelta(days=365)
        out_ly_start = in_ly_start
        out_ly_end = in_ly_end
        inside_daily: list[dict] = []
        outside_daily: list[dict] = []

        try:
            if self.data_source == DATA_SOURCE_INFLUXDB and self.influxdb_client:
                inside_avg = await get_period_average_influxdb(
                    self.influxdb_client, self.inside_entity, period_start, now
                )
                outside_avg = await get_period_average_influxdb(
                    self.influxdb_client, self.outside_entity, period_start, now
                )

                inside_ly, in_ly_start, in_ly_end = await get_last_year_average_influxdb(
                    self.influxdb_client, self.inside_entity, self.history_days
                )
                outside_ly, out_ly_start, out_ly_end = await get_last_year_average_influxdb(
                    self.influxdb_client, self.outside_entity, self.history_days
                )

                # Sparkline data (last 14 days)
                sparkline_start = now - timedelta(days=14)
                inside_daily = await get_daily_means_influxdb(
                    self.influxdb_client, self.inside_entity, sparkline_start, now
                )
                outside_daily = await get_daily_means_influxdb(
                    self.influxdb_client, self.outside_entity, sparkline_start, now
                )
            else:
                inside_avg = await get_period_average(
                    self.hass, self.inside_entity, period_start, now
                )
                outside_avg = await get_period_average(
                    self.hass, self.outside_entity, period_start, now
                )

                inside_ly, in_ly_start, in_ly_end = await get_last_year_average(
                    self.hass, self.inside_entity, self.history_days
                )
                outside_ly, out_ly_start, out_ly_end = await get_last_year_average(
                    self.hass, self.outside_entity, self.history_days
                )

                # Sparkline data (last 14 days)
                sparkline_start = now - timedelta(days=14)
                inside_daily = await get_daily_means(
                    self.hass, self.inside_entity, sparkline_start, now
                )
                outside_daily = await get_daily_means(
                    self.hass, self.outside_entity, sparkline_start, now
                )
        except Exception:
            _LOGGER.warning("Failed to fetch statistics, using current values only", exc_info=True)

        # Compute corrected difference
        corrected = None
        trend = "unknown"
        if all(v is not None for v in [inside_avg, inside_ly, outside_avg, outside_ly]):
            inside_diff = inside_ly - inside_avg
            outdoor_correction = (outside_avg - outside_ly) * self.weight_outdoor
            corrected = inside_diff + outdoor_correction
            if corrected > 0.3:
                trend = "cooler"
            elif corrected < -0.3:
                trend = "warmer"
            else:
                trend = "similar"

        return TemperatureComparisonData(
            inside_current=inside_current,
            outside_current=outside_current,
            inside_avg_period=round(inside_avg, 2) if inside_avg is not None else None,
            outside_avg_period=round(outside_avg, 2) if outside_avg is not None else None,
            inside_avg_last_year=round(inside_ly, 2) if inside_ly is not None else None,
            outside_avg_last_year=round(outside_ly, 2) if outside_ly is not None else None,
            inside_last_year_start=in_ly_start.isoformat(),
            inside_last_year_end=in_ly_end.isoformat(),
            outside_last_year_start=out_ly_start.isoformat(),
            outside_last_year_end=out_ly_end.isoformat(),
            corrected_difference=round(corrected, 2) if corrected is not None else None,
            trend=trend,
            inside_daily_history=inside_daily,
            outside_daily_history=outside_daily,
            history_days=self.history_days,
            weight_outdoor=self.weight_outdoor,
        )

    def _get_entity_value(self, entity_id: str) -> float | None:
        """Get the current numeric value of an entity."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        try:
            return round(float(state.state), 2)
        except (ValueError, TypeError):
            return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Temperature Comparison from a config entry."""
    inside_entity = entry.data[CONF_INSIDE_ENTITY]
    outside_entity = entry.data[CONF_OUTSIDE_ENTITY]
    history_days = entry.options.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS)
    weight_outdoor = entry.options.get(CONF_WEIGHT_OUTDOOR, DEFAULT_WEIGHT_OUTDOOR)
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    data_source = entry.data.get(CONF_DATA_SOURCE, DATA_SOURCE_RECORDER)

    influxdb_client = None
    if data_source == DATA_SOURCE_INFLUXDB:
        # Get InfluxDB config from HA's influxdb integration
        influxdb_config = hass.data.get("influxdb", {})
        if isinstance(influxdb_config, dict):
            host = influxdb_config.get("host") or influxdb_config.get("url", "").split("://")[-1].split(":")[0]
            port = influxdb_config.get("port", 8086)
            token = influxdb_config.get("token")
            org = influxdb_config.get("org", "home-assistant")
            bucket = influxdb_config.get("bucket", "homeassistant")

            if host and token:
                influxdb_client = InfluxDBClient(
                    host=host,
                    port=port,
                    token=token,
                    org=org,
                    bucket=bucket,
                )
                _LOGGER.info("Using HA's InfluxDB integration at %s:%d for temperature data", host, port)
            else:
                _LOGGER.warning("InfluxDB data source selected but HA's InfluxDB integration not found or not configured, falling back to recorder")
                data_source = DATA_SOURCE_RECORDER
        else:
            _LOGGER.warning("InfluxDB data source selected but HA's InfluxDB integration not configured, falling back to recorder")
            data_source = DATA_SOURCE_RECORDER

    coordinator = TemperatureComparisonCoordinator(
        hass,
        inside_entity,
        outside_entity,
        history_days,
        weight_outdoor,
        update_interval,
        data_source=data_source,
        influxdb_client=influxdb_client,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register Lovelace card
    card_key = f"{DOMAIN}_card_registered"
    if card_key not in hass.data:
        card_url = f"/{DOMAIN}/temperature-comparison-card.js"
        card_path = str(Path(__file__).parent / "www" / "temperature-comparison-card.js")
        await hass.http.async_register_static_paths(
            [StaticPathConfig(card_url, card_path, False)]
        )
        integration = await async_get_integration(hass, DOMAIN)
        add_extra_js_url(hass, f"{card_url}?v={integration.version}")
        hass.data[card_key] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
