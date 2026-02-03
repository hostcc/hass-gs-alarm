# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Ilia Sotnikov
"""
Config flow for `gs_alarm` integrarion.
"""

from __future__ import annotations
import logging

from typing import Any, Self, Dict

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from pyg90alarm import G90Alarm
from pyg90alarm.const import (
    LOCAL_CLOUD_NOTIFICATIONS_PORT, REMOTE_CLOUD_PORT,
)

from .const import (
    DOMAIN,
    CONF_NOTIFICATIONS_PROTOCOL,
    CONF_IP_ADDR,
    CONF_CLOUD_IP,
    CONF_CLOUD_PORT,
    CONF_CLOUD_LOCAL_PORT,
    CONF_CLOUD_UPSTREAM_HOST,
    CONF_CLOUD_UPSTREAM_PORT,
    CONF_OPT_NOTIFICATIONS_LOCAL,
    CONF_OPT_NOTIFICATIONS_CLOUD,
    CONF_OPT_NOTIFICATIONS_CLOUD_UPSTREAM,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDR, default=False): str,
    },
)


class G90ConfigFlow(ConfigFlow, domain=DOMAIN):
    """
    Handles the config flow for `gs_alarm` integration.
    """
    VERSION = 1

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Handles discovering devices upon user confirmation.
        """
        if user_input is None:
            self._set_confirm_only()
            return self.async_show_form(step_id="confirm")

        devices = await self.hass.async_create_task(G90Alarm.discover())
        _LOGGER.debug('Discovered devices: %s', devices)
        # No devices discovered, present form for manual hostname/IP entry
        if not devices:
            return await self.async_step_custom_host(None)

        # Instantiate the integration for discovered devices
        # Need to properly handle the result for multiple devices
        for device in devices:
            res = self.async_create_entry(
                title=DOMAIN, data={CONF_IP_ADDR: device.host}
            )
        return res

    async def async_step_user(
        self, _user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Handles the initial step.
        """
        return await self.async_step_confirm(None)

    async def async_step_custom_host(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Handles adding integration with manual hostname/IP specified.
        """
        if user_input is None:
            return self.async_show_form(
                step_id='custom_host',
                data_schema=STEP_USER_DATA_SCHEMA
            )
        errors = {}

        # Register the integration when hostname/IP is provided
        if not user_input.get(CONF_IP_ADDR, None):
            errors[CONF_IP_ADDR] = 'ip_addr_required'
        else:
            return self.async_create_entry(title=DOMAIN, data=user_input)

        # Hostname/IP address is required
        return self.async_show_form(
            step_id='custom_host',
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry
    ) -> OptionsFlowHandler:
        """
        Instantiates options flow handler.
        """
        return OptionsFlowHandler()

    def is_matching(self, other_flow: Self) -> bool:
        """
        Determine if there is another flow for the same entity running already.

        Not currently implemented, and only used to prevent `pylint` from
        erroring out stating the method is abstract in the base class:

            W0223: Method 'is_matching' is abstract in class 'ConfigFlow' but
            is not overridden in child class 'G90ConfigFlow' (abstract-method)
        """
        raise NotImplementedError


class OptionsFlowHandler(OptionsFlow):
    """
    Handle options (configure) flows.
    """
    # pylint:disable=too-few-public-methods
    # Data from the initial step is stored here, since cloud options will
    # use second step merging the input with the data from the first step
    init_step_data: Dict[str, Any] = {}

    @property
    def common_cloud_notifications_schema(self) -> vol.Schema:
        """
        Returns the common schema for cloud notifications configuration.
        """
        return vol.Schema(
            {
                vol.Required(
                    CONF_CLOUD_IP,
                    default=self.config_entry.options.get(
                        CONF_CLOUD_IP, None
                    )
                ): str,
                vol.Required(
                    CONF_CLOUD_PORT,
                    default=self.config_entry.options.get(
                        CONF_CLOUD_PORT, REMOTE_CLOUD_PORT
                    )
                ): int,
                vol.Required(
                    CONF_CLOUD_LOCAL_PORT,
                    default=self.config_entry.options.get(
                        CONF_CLOUD_LOCAL_PORT, LOCAL_CLOUD_NOTIFICATIONS_PORT
                    )
                ): int,
            }
        )

    async def set_cloud_server_address(
        self, user_input: dict[str, Any]
    ) -> None:
        """
        Sets the cloud server address on the client.

        The reason the operation is under options flow is that the
        cloud server address should only be done once, not every time the
        integration starts.

        :param user_input: The user input containing cloud server
         configuration.
        """
        _LOGGER.debug(
            "Setting cloud server address to %s:%d",
            user_input[CONF_CLOUD_IP],
            user_input[CONF_CLOUD_PORT],
        )
        await self.config_entry.runtime_data.client.set_cloud_server_address(
            cloud_ip=user_input[CONF_CLOUD_IP],
            cloud_port=user_input[CONF_CLOUD_PORT],
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Manage the options.
        """
        schema: dict[
            vol.Required | vol.Optional,
            SelectSelector | BooleanSelector
        ] = {
            vol.Required(
                CONF_NOTIFICATIONS_PROTOCOL,
                default=self.config_entry.options.get(
                    CONF_NOTIFICATIONS_PROTOCOL, CONF_OPT_NOTIFICATIONS_CLOUD
                ),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        CONF_OPT_NOTIFICATIONS_CLOUD,
                        CONF_OPT_NOTIFICATIONS_LOCAL,
                        CONF_OPT_NOTIFICATIONS_CLOUD_UPSTREAM,
                    ],
                    multiple=False,
                    mode=SelectSelectorMode.LIST,
                    translation_key=CONF_NOTIFICATIONS_PROTOCOL,
                )
            ),
        }

        # Present the form back if no user input
        if user_input is None:
            return self.async_show_form(
                step_id='init',
                data_schema=vol.Schema(schema),
                last_step=False,
            )

        # Store the user input from the first step
        self.init_step_data = user_input
        if user_input.get(CONF_NOTIFICATIONS_PROTOCOL) == (
            CONF_OPT_NOTIFICATIONS_CLOUD
        ):
            return await self.async_step_cloud()

        if user_input.get(CONF_NOTIFICATIONS_PROTOCOL) == (
            CONF_OPT_NOTIFICATIONS_CLOUD_UPSTREAM
        ):
            return await self.async_step_cloud_upstream()

        # (Re)create the integration entry, that will fetch the options and
        # adjust its configuration
        return self.async_create_entry(title=DOMAIN, data=user_input)

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Handles the cloud configuration.
        """
        if user_input is None:
            return self.async_show_form(
                    step_id='cloud',
                    data_schema=self.common_cloud_notifications_schema,
                    last_step=True,
                )

        # Merge the user input with the data from the first step to create
        # the final configuration
        user_input.update(self.init_step_data)

        # Set cloud server address immediately
        await self.set_cloud_server_address(user_input)

        # Create the entry with updated options
        return self.async_create_entry(title=DOMAIN, data=user_input)

    async def async_step_cloud_upstream(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """
        Handles the cloud upstream configuration.
        """
        schema = self.common_cloud_notifications_schema.extend({
                vol.Required(
                    CONF_CLOUD_UPSTREAM_HOST,
                    default=self.config_entry.options.get(
                        CONF_CLOUD_UPSTREAM_HOST
                    )
                ): str,
                vol.Required(
                    CONF_CLOUD_UPSTREAM_PORT,
                    default=self.config_entry.options.get(
                        CONF_CLOUD_UPSTREAM_PORT
                    )
                ): int,
            }
        )

        if user_input is None:
            return self.async_show_form(
                    step_id='cloud_upstream',
                    data_schema=schema,
                    last_step=True,
                )

        # Merge the user input with the data from the first step to create
        # the final configuration
        user_input.update(self.init_step_data)

        # Set cloud server address immediately
        await self.set_cloud_server_address(user_input)

        # Create the entry with updated options
        return self.async_create_entry(title=DOMAIN, data=user_input)
