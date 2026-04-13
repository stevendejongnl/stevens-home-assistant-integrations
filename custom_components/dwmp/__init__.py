"""The Dude, Where's My Package? integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.loader import async_get_integration

from .api_client import DWMPApiClient, DWMPApiError, DWMPAuthError, DWMPConnectionError
from .const import ACTIVE_STATUSES, CONF_TOKEN, CONF_URL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


@dataclass
class DWMPData:
    """Data returned by the DWMP coordinator."""

    packages: list[dict] = field(default_factory=list)
    package_details: dict[int, dict] = field(default_factory=dict)
    version: str = ""


class DWMPCoordinator(DataUpdateCoordinator[DWMPData]):
    """Coordinator that polls the DWMP API."""

    def __init__(self, hass: HomeAssistant, client: DWMPApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self._previous_notification_ids: set[int] = set()

    async def _async_update_data(self) -> DWMPData:
        try:
            packages = await self.client.list_packages()

            # Fetch event timeline for active packages
            details: dict[int, dict] = {}
            for pkg in packages:
                if pkg.get("current_status") in ACTIVE_STATUSES:
                    try:
                        detail = await self.client.get_package(pkg["id"])
                        details[pkg["id"]] = detail
                    except Exception:
                        _LOGGER.debug("Failed to fetch details for package %s", pkg["id"])

            # Check for new notifications to fire HA events
            try:
                notifications = await self.client.list_notifications(limit=20)
                current_ids = {n["id"] for n in notifications}
                new_ids = current_ids - self._previous_notification_ids
                if self._previous_notification_ids:
                    for notification in notifications:
                        if notification["id"] in new_ids:
                            self.hass.bus.async_fire(
                                "dwmp_package_status_changed",
                                {
                                    "tracking_number": notification.get("tracking_number"),
                                    "carrier": notification.get("carrier"),
                                    "label": notification.get("label"),
                                    "old_status": notification.get("old_status"),
                                    "new_status": notification.get("new_status"),
                                },
                            )
                self._previous_notification_ids = current_ids
            except Exception:
                _LOGGER.debug("Failed to fetch notifications for event firing")

            version = ""
            try:
                health = await self.client.health()
                version = health.get("version", "")
            except Exception:
                pass

            return DWMPData(
                packages=packages,
                package_details=details,
                version=version,
            )

        except DWMPAuthError as err:
            raise ConfigEntryAuthFailed("Token expired or invalid") from err
        except (DWMPConnectionError, DWMPApiError) as err:
            raise UpdateFailed(str(err)) from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DWMP from a config entry."""
    session = async_get_clientsession(hass)
    client = DWMPApiClient(session, entry.data[CONF_URL], entry.data[CONF_TOKEN])

    coordinator = DWMPCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register Lovelace card
    card_key = f"{DOMAIN}_card_registered"
    if card_key not in hass.data:
        card_url = f"/{DOMAIN}/dwmp-tracking-card.js"
        card_path = str(Path(__file__).parent / "www" / "dwmp-tracking-card.js")
        await hass.http.async_register_static_paths(
            [StaticPathConfig(card_url, card_path, False)]
        )
        integration = await async_get_integration(hass, DOMAIN)
        add_extra_js_url(hass, f"{card_url}?v={integration.version}")
        hass.data[card_key] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a DWMP config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
