"""Config flow for gs_alarm."""

from __future__ import annotations
import logging

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectSelector,
    SelectSelectorConfig,
    SelectOptionDict,
)
from pyg90alarm import G90Alarm

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("ip_addr"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for gs_alarm."""

    VERSION = 1

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """ tbd """
        if user_input is None:
            self._set_confirm_only()
            return self.async_show_form(step_id="confirm")

        devices = await self.hass.async_create_task(G90Alarm.discover())
        if not devices:
            return await self.async_step_custom_host(None)
        # Need to extend to handle multiple devices
        for device in devices:
            res = self.async_create_entry(
                title=DOMAIN, data={'ip_addr': device['host']}
            )
        return res

    async def async_step_user(
        self, _user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        return await self.async_step_confirm(None)

    async def async_step_custom_host(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """ tbd """
        if user_input is None:
            return self.async_show_form(
                step_id="custom_host", data_schema=STEP_USER_DATA_SCHEMA
            )
        errors = {}

        if not user_input.get('ip_addr', None):
            errors['ip_addr'] = 'ip_addr_required'
        else:
            return self.async_create_entry(title=DOMAIN, data=user_input)

        return self.async_show_form(
            step_id="custom_host", data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """ tbd """
        return OptionsFlowHandler(config_entry)


# pylint:disable=too-few-public-methods
class OptionsFlowHandler(config_entries.OptionsFlow):
    """ tbd """
    def __init__(self, config_entry):
        """ Initialize options flow. """
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """ Manage the options. """
        g90_client = (
            self.hass.data[DOMAIN]
            .get(self.config_entry.entry_id, {})
            .get('client', None)
        )
        schema = {
            vol.Required(
                "sms_alert_when_armed",
                default=self.config_entry.options.get(
                    "sms_alert_when_armed", False
                ),
            ): BooleanSelector(),
        }

        disabled_sensors = []
        all_sensors = []
        sensors_unsupported = []
        if g90_client:
            g90_sensors = await g90_client.get_sensors()
            all_sensors = [
                SelectOptionDict(label=x.name, value=str(x.index))
                for x in g90_sensors
            ]
            disabled_sensors = [
                str(x.index) for x in g90_sensors if not x.enabled
            ]
            sensors_unsupported = [
                str(x.index) for x in g90_sensors
                if not x.supports_enable_disable
            ]
            schema.update({
                vol.Optional(
                    "disabled_sensors",
                    default=disabled_sensors
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=all_sensors,
                        multiple=True,
                    )
                ),
            })

        if user_input is None:
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(schema)
            )

        errors = {}
        if user_input is not None:
            if sensors_unsupported in user_input.get('disabled_sensors', []):
                errors['disabled_sensors'] = 'sensor_no_enable_disable_support'
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            errors=errors
        )
