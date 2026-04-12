"""Config flow for Dude, Where's My Package?"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api_client import DWMPApiClient, DWMPAuthError, DWMPConnectionError
from .const import CONF_PASSWORD, CONF_TOKEN, CONF_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class DWMPConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DWMP."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Handle the initial configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            password = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            client = DWMPApiClient(session, url)

            try:
                await client.health()
            except DWMPConnectionError:
                errors["base"] = "cannot_connect"
            else:
                try:
                    token = await client.get_token(password)
                except DWMPAuthError:
                    errors["base"] = "invalid_auth"
                except DWMPConnectionError:
                    errors["base"] = "cannot_connect"
                else:
                    hostname = urlparse(url).hostname or url
                    await self.async_set_unique_id(hostname)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="Dude, Where's My Package?",
                        data={CONF_URL: url, CONF_TOKEN: token},
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict
    ) -> ConfigFlowResult:
        """Handle re-authentication when the token expires."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            reauth_entry = self._get_reauth_entry()
            url = reauth_entry.data[CONF_URL]
            password = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            client = DWMPApiClient(session, url)

            try:
                token = await client.get_token(password)
            except DWMPAuthError:
                errors["base"] = "invalid_auth"
            except DWMPConnectionError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data={CONF_URL: url, CONF_TOKEN: token},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
