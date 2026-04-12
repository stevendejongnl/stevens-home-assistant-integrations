"""Sensor platform for Dude, Where's My Package?"""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DWMPCoordinator, DWMPData
from .const import ACTIVE_STATUSES, CONF_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DWMP sensors from a config entry."""
    coordinator: DWMPCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([DWMPPackagesSensor(coordinator, entry)])


class DWMPPackagesSensor(CoordinatorEntity[DWMPCoordinator], SensorEntity):
    """Sensor showing tracked packages with their events."""

    _attr_has_entity_name = True
    _attr_name = "Packages"
    _attr_icon = "mdi:package-variant"
    _attr_native_unit_of_measurement = "packages"

    def __init__(
        self,
        coordinator: DWMPCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_packages"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Dude, Where's My Package?",
            manufacturer="MadeBySteven",
            sw_version=coordinator.data.version if coordinator.data else None,
            configuration_url=entry.data[CONF_URL],
        )

    @property
    def _data(self) -> DWMPData:
        return self.coordinator.data

    @property
    def native_value(self) -> int:
        """State = number of active packages."""
        return len([
            p for p in self._data.packages
            if p.get("current_status") in ACTIVE_STATUSES
        ])

    @property
    def extra_state_attributes(self) -> dict:
        active = []
        delivered = []

        for pkg in self._data.packages:
            status = pkg.get("current_status")
            detail = self._data.package_details.get(pkg["id"], pkg)
            events = detail.get("events", [])

            pkg_data = {
                "id": pkg["id"],
                "tracking_number": pkg.get("tracking_number"),
                "carrier": pkg.get("carrier"),
                "status": status,
                "label": pkg.get("label"),
                "estimated_delivery": pkg.get("estimated_delivery"),
                "updated_at": pkg.get("updated_at"),
            }

            if status in ACTIVE_STATUSES:
                pkg_data["events"] = [
                    {
                        "timestamp": e.get("timestamp"),
                        "status": e.get("status"),
                        "description": e.get("description"),
                        "location": e.get("location"),
                    }
                    for e in events
                ]
                active.append(pkg_data)
            else:
                delivered.append(pkg_data)

        return {
            "active": active,
            "delivered": delivered,
            "total_active": len(active),
            "total_delivered": len(delivered),
        }
