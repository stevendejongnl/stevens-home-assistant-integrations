"""Sensor platform for Temperature Comparison."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TemperatureComparisonCoordinator, TemperatureComparisonData
from .const import CONF_INSIDE_ENTITY, CONF_NAME, CONF_OUTSIDE_ENTITY, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Temperature Comparison sensors from a config entry."""
    coordinator: TemperatureComparisonCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            InsideAverageSensor(coordinator, entry),
            OutsideAverageSensor(coordinator, entry),
            InsideLastYearSensor(coordinator, entry),
            OutsideLastYearSensor(coordinator, entry),
            CorrectedDifferenceSensor(coordinator, entry),
        ]
    )


class TemperatureComparisonSensorBase(
    CoordinatorEntity[TemperatureComparisonCoordinator], SensorEntity
):
    """Base class for Temperature Comparison sensors."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: TemperatureComparisonCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        name = entry.data.get(CONF_NAME, DEFAULT_NAME)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=name,
            manufacturer="MadeBySteven",
        )

    @property
    def _data(self) -> TemperatureComparisonData:
        return self.coordinator.data


class InsideAverageSensor(TemperatureComparisonSensorBase):
    """Sensor showing the rolling average inside temperature."""

    _attr_name = "Inside average"
    _attr_icon = "mdi:home-thermometer"

    def __init__(self, coordinator: TemperatureComparisonCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_inside_average"

    @property
    def native_value(self) -> float | None:
        return self._data.inside_avg_period

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "current_temperature": self._data.inside_current,
            "source_entity": self._entry.data[CONF_INSIDE_ENTITY],
            "period_days": self._data.history_days,
            "daily_values": self._data.inside_daily_history,
        }


class OutsideAverageSensor(TemperatureComparisonSensorBase):
    """Sensor showing the rolling average outside temperature."""

    _attr_name = "Outside average"
    _attr_icon = "mdi:thermometer"

    def __init__(self, coordinator: TemperatureComparisonCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_outside_average"

    @property
    def native_value(self) -> float | None:
        return self._data.outside_avg_period

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "current_temperature": self._data.outside_current,
            "source_entity": self._entry.data[CONF_OUTSIDE_ENTITY],
            "period_days": self._data.history_days,
            "daily_values": self._data.outside_daily_history,
        }


class InsideLastYearSensor(TemperatureComparisonSensorBase):
    """Sensor showing the inside average from the same period last year."""

    _attr_name = "Inside last year"
    _attr_icon = "mdi:home-thermometer-outline"
    _attr_state_class = None

    def __init__(self, coordinator: TemperatureComparisonCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_inside_last_year"

    @property
    def native_value(self) -> float | None:
        return self._data.inside_avg_last_year

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "source_entity": self._entry.data[CONF_INSIDE_ENTITY],
            "period_start": self._data.inside_last_year_start,
            "period_end": self._data.inside_last_year_end,
        }


class OutsideLastYearSensor(TemperatureComparisonSensorBase):
    """Sensor showing the outside average from the same period last year."""

    _attr_name = "Outside last year"
    _attr_icon = "mdi:thermometer-lines"
    _attr_state_class = None

    def __init__(self, coordinator: TemperatureComparisonCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_outside_last_year"

    @property
    def native_value(self) -> float | None:
        return self._data.outside_avg_last_year

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "source_entity": self._entry.data[CONF_OUTSIDE_ENTITY],
            "period_start": self._data.outside_last_year_start,
            "period_end": self._data.outside_last_year_end,
        }


class CorrectedDifferenceSensor(TemperatureComparisonSensorBase):
    """Sensor showing the year-over-year corrected temperature difference."""

    _attr_name = "Corrected difference"
    _attr_icon = "mdi:swap-vertical"
    _attr_state_class = None

    def __init__(self, coordinator: TemperatureComparisonCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_corrected_difference"

    @property
    def native_value(self) -> float | None:
        return self._data.corrected_difference

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "trend": self._data.trend,
            "weight_outdoor_correction": self._data.weight_outdoor,
            "formula": "(inside_last_year - inside_now) + (outside_now - outside_last_year) * weight",
            "components": {
                "inside_avg": self._data.inside_avg_period,
                "inside_last_year": self._data.inside_avg_last_year,
                "outside_avg": self._data.outside_avg_period,
                "outside_last_year": self._data.outside_avg_last_year,
            },
        }
