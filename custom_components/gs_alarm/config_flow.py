"""Config flow for gs_alarm."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback

from .const import DOMAIN

from pyg90alarm import G90Alarm

import logging

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
        if user_input is None:
            self._set_confirm_only()
            return self.async_show_form(step_id="confirm")

        devices = await self.hass.async_create_task(G90Alarm.discover())
        if not devices:
            return await self.async_step_custom_host(None)
        # FIXME: Handle multiple devices
        for device in devices:
            res = self.async_create_entry(title=DOMAIN, data={'ip_addr': device['host']})
        return res

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        return await self.async_step_confirm(None)

    async def async_step_custom_host(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="custom_host", data_schema=STEP_USER_DATA_SCHEMA
            )
        errors = {}

        if not user_input.get('ip_addr', None):
            errors['base'] = 'ip_addr_required'
        else:
            return self.async_create_entry(title=DOMAIN, data=user_input)

        return self.async_show_form(
            step_id="custom_host", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        """ Initialize options flow. """
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """ Manage the options. """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "sms_alert_when_armed",
                        default=self.config_entry.options.get("sms_alert_when_armed"),
                    ): bool
                }
            ),
        )
