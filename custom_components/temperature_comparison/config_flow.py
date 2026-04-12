"""Config flow for Temperature Comparison."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_HISTORY_DAYS,
    CONF_INSIDE_ENTITY,
    CONF_NAME,
    CONF_OUTSIDE_ENTITY,
    CONF_UPDATE_INTERVAL,
    CONF_WEIGHT_OUTDOOR,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_WEIGHT_OUTDOOR,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class TemperatureComparisonConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Temperature Comparison."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Handle the initial configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            inside = user_input[CONF_INSIDE_ENTITY]
            outside = user_input[CONF_OUTSIDE_ENTITY]

            if inside == outside:
                errors["base"] = "same_entity"
            else:
                # Verify entities exist and have numeric states
                for entity_id in (inside, outside):
                    state = self.hass.states.get(entity_id)
                    if state is None:
                        errors["base"] = "entity_not_found"
                        break

                if not errors:
                    unique_id = f"{inside}_{outside}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    name = user_input.get(CONF_NAME, DEFAULT_NAME)
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_INSIDE_ENTITY: inside,
                            CONF_OUTSIDE_ENTITY: outside,
                            CONF_NAME: name,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INSIDE_ENTITY): EntitySelector(
                        EntitySelectorConfig(
                            domain="sensor",
                            device_class=SensorDeviceClass.TEMPERATURE,
                        )
                    ),
                    vol.Required(CONF_OUTSIDE_ENTITY): EntitySelector(
                        EntitySelectorConfig(
                            domain="sensor",
                            device_class=SensorDeviceClass.TEMPERATURE,
                        )
                    ),
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return TemperatureComparisonOptionsFlow(config_entry)


class TemperatureComparisonOptionsFlow(OptionsFlow):
    """Handle options for Temperature Comparison."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_HISTORY_DAYS,
                        default=self._config_entry.options.get(
                            CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1, max=30, step=1, mode=NumberSelectorMode.SLIDER
                        )
                    ),
                    vol.Optional(
                        CONF_WEIGHT_OUTDOOR,
                        default=self._config_entry.options.get(
                            CONF_WEIGHT_OUTDOOR, DEFAULT_WEIGHT_OUTDOOR
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0.0, max=2.0, step=0.1, mode=NumberSelectorMode.SLIDER
                        )
                    ),
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=300, max=7200, step=300, mode=NumberSelectorMode.SLIDER,
                            unit_of_measurement="seconds",
                        )
                    ),
                }
            ),
        )
