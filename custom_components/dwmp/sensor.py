"""Sensor platform for Dude, Where's My Package?"""

from __future__ import annotations

from datetime import datetime, timezone
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
    coordinator: DWMPCoordinator = entry.runtime_data

    async_add_entities(
        [
            DWMPActivePackagesSensor(coordinator, entry),
            DWMPDeliveredTodaySensor(coordinator, entry),
            DWMPUnreadNotificationsSensor(coordinator, entry),
        ]
    )


class DWMPSensorBase(CoordinatorEntity[DWMPCoordinator], SensorEntity):
    """Base class for DWMP sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DWMPCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
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


class DWMPActivePackagesSensor(DWMPSensorBase):
    """Sensor showing the count of active (non-delivered) packages."""

    _attr_name = "Active packages"
    _attr_icon = "mdi:package-variant"
    _attr_native_unit_of_measurement = "packages"

    def __init__(self, coordinator: DWMPCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_active_packages"

    @property
    def native_value(self) -> int:
        active = [
            p for p in self._data.packages
            if p.get("current_status") in ACTIVE_STATUSES
        ]
        return len(active)

    @property
    def extra_state_attributes(self) -> dict:
        packages = []
        for pkg in self._data.packages:
            if pkg.get("current_status") not in ACTIVE_STATUSES:
                continue
            detail = self._data.package_details.get(pkg["id"], pkg)
            events = detail.get("events", [])
            packages.append(
                {
                    "id": pkg["id"],
                    "tracking_number": pkg.get("tracking_number"),
                    "carrier": pkg.get("carrier"),
                    "status": pkg.get("current_status"),
                    "label": pkg.get("label"),
                    "estimated_delivery": pkg.get("estimated_delivery"),
                    "updated_at": pkg.get("updated_at"),
                    "events": [
                        {
                            "timestamp": e.get("timestamp"),
                            "status": e.get("status"),
                            "description": e.get("description"),
                            "location": e.get("location"),
                        }
                        for e in events
                    ],
                }
            )
        return {"packages": packages}


class DWMPDeliveredTodaySensor(DWMPSensorBase):
    """Sensor showing the count of packages delivered today."""

    _attr_name = "Delivered today"
    _attr_icon = "mdi:package-variant-closed-check"
    _attr_native_unit_of_measurement = "packages"

    def __init__(self, coordinator: DWMPCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_delivered_today"

    @property
    def native_value(self) -> int:
        today = datetime.now(timezone.utc).date()
        count = 0
        for pkg in self._data.packages:
            if pkg.get("current_status") != "delivered":
                continue
            updated = pkg.get("updated_at", "")
            try:
                pkg_date = datetime.fromisoformat(updated).date()
                if pkg_date == today:
                    count += 1
            except (ValueError, TypeError):
                pass
        return count

    @property
    def extra_state_attributes(self) -> dict:
        today = datetime.now(timezone.utc).date()
        packages = []
        for pkg in self._data.packages:
            if pkg.get("current_status") != "delivered":
                continue
            updated = pkg.get("updated_at", "")
            try:
                pkg_date = datetime.fromisoformat(updated).date()
                if pkg_date != today:
                    continue
            except (ValueError, TypeError):
                continue
            packages.append(
                {
                    "tracking_number": pkg.get("tracking_number"),
                    "carrier": pkg.get("carrier"),
                    "label": pkg.get("label"),
                }
            )
        return {"packages": packages}


class DWMPUnreadNotificationsSensor(DWMPSensorBase):
    """Sensor showing unread notification count."""

    _attr_name = "Unread notifications"
    _attr_icon = "mdi:bell-badge"
    _attr_native_unit_of_measurement = "notifications"

    def __init__(self, coordinator: DWMPCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_unread_notifications"

    @property
    def native_value(self) -> int:
        return self._data.unread_count

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "notifications": [
                {
                    "tracking_number": n.get("tracking_number"),
                    "carrier": n.get("carrier"),
                    "old_status": n.get("old_status"),
                    "new_status": n.get("new_status"),
                    "label": n.get("label"),
                    "is_read": bool(n.get("is_read")),
                    "created_at": n.get("created_at"),
                }
                for n in self._data.notifications
            ]
        }
