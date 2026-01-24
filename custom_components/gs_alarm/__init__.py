# SPDX-License-Identifier: MIT
# Copyright (c) 2021 Ilia Sotnikov
"""
The `gs_alarm` integration.
"""
from __future__ import annotations
from typing import Any, cast, TYPE_CHECKING
from types import MappingProxyType
import asyncio
import logging

from pyg90alarm import (
    G90Alarm, G90Error, G90TimeoutError,
)
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryNotReady, ConfigEntryError
)

from .const import (
    CONF_IP_ADDR,
    CONF_NOTIFICATIONS_PROTOCOL,
    CONF_CLOUD_LOCAL_PORT,
    CONF_CLOUD_UPSTREAM_HOST,
    CONF_CLOUD_UPSTREAM_PORT,
    CONF_OPT_NOTIFICATIONS_LOCAL,
    CONF_OPT_NOTIFICATIONS_CLOUD,
    CONF_OPT_NOTIFICATIONS_CLOUD_UPSTREAM,
)
from .coordinator import GsAlarmCoordinator
if TYPE_CHECKING:
    type GsAlarmConfigEntry = ConfigEntry[GsAlarmCoordinator]

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [
    "alarm_control_panel", "switch", "binary_sensor", "sensor", "select",
    "button", "text", "number"
]


async def _options_notifications_protocol(
    g90_client: G90Alarm, options: MappingProxyType[str, Any]
) -> None:
    """
    Configure the selected notifications protocol during options (configure)
    flow
    """
    # Protocol defaults to local notifications if not set in the options
    # (e.g. during initial component setup)
    notifications_protocol = options.get(
        CONF_NOTIFICATIONS_PROTOCOL, CONF_OPT_NOTIFICATIONS_LOCAL
    )

    # Local notifications protocol has been selected
    if notifications_protocol == CONF_OPT_NOTIFICATIONS_LOCAL:
        _LOGGER.debug(
            'Using local notifications protocol'
        )
        await g90_client.use_local_notifications()

    if notifications_protocol in [CONF_OPT_NOTIFICATIONS_CLOUD,
                                  CONF_OPT_NOTIFICATIONS_CLOUD_UPSTREAM]:
        # Cloud notifications protocol requires local port to be set
        cloud_local_port = options.get(CONF_CLOUD_LOCAL_PORT)
        if cloud_local_port is None:
            raise ConfigEntryError(
                f"'{CONF_CLOUD_LOCAL_PORT}' option is required"
            )

    # Cloud notifications protocol has been selected
    if notifications_protocol == CONF_OPT_NOTIFICATIONS_CLOUD:
        _LOGGER.debug(
            'Using cloud notifications protocol:'
            ' local port %d',
            cloud_local_port
        )
        await g90_client.use_cloud_notifications(
            cloud_local_port=cast(int, cloud_local_port),
            upstream_host=None,
            upstream_port=None
        )

    # Chained cloud notifications protocol has been selected
    if notifications_protocol == CONF_OPT_NOTIFICATIONS_CLOUD_UPSTREAM:
        cloud_upstream_host = options.get(CONF_CLOUD_UPSTREAM_HOST)
        cloud_upstream_port = options.get(CONF_CLOUD_UPSTREAM_PORT)

        _LOGGER.debug(
            'Using chained cloud notifications protocol:'
            " local port %d, host '%s', port %d",
            cloud_local_port, cloud_upstream_host, cloud_upstream_port
        )
        await g90_client.use_cloud_notifications(
            cloud_local_port=cast(int, cloud_local_port),
            upstream_host=cloud_upstream_host,
            upstream_port=cloud_upstream_port
        )

    # Start listening for notifications
    await g90_client.listen_notifications()


async def options_update_listener(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry
) -> None:
    """
    Handles options update.
    """
    try:
        g90_client = entry.runtime_data.client
        _LOGGER.debug(
            'Updating alarm panel from config_entry options %s',
            entry.options
        )

        # Configure the selected notifications protocol
        await _options_notifications_protocol(g90_client, entry.options)
    except G90TimeoutError as exc:
        raise ConfigEntryNotReady(
            f"Timeout while connecting to '{g90_client.host}'"
        ) from exc
    except G90Error as exc:
        raise ConfigEntryError(f"'{g90_client.host}': {repr(exc)}") from exc


async def async_setup_entry(
    hass: HomeAssistant, entry: GsAlarmConfigEntry
) -> bool:
    """
    Sets up gs_alarm from a config entry.
    """
    host = entry.data.get(CONF_IP_ADDR, None)
    try:
        g90_client = G90Alarm(host)
        coordinator = GsAlarmCoordinator(hass, entry, g90_client)
        # Fetch essential data into the coordinator, since setting up the
        # below platforms depend on it to generate IDs and device info
        await coordinator.init_essential_data()
        entry.runtime_data = coordinator
    except G90TimeoutError as exc:
        raise ConfigEntryNotReady(
            f"Timeout while connecting to '{host}'"
        ) from exc
    except G90Error as exc:
        raise ConfigEntryError(f"'{host}': {repr(exc)}") from exc

    # Should be called before coordinator initial refresh to have callbacks
    # registered for sensor and device lists, otherwise corresponding HASS
    # entities won't get added
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    # Perform the initial data refresh
    await entry.runtime_data.async_config_entry_first_refresh()

    # Update the entry's title
    if not hass.config_entries.async_update_entry(
        entry, title=coordinator.data.host_info.host_guid
    ):
        # Force setting options upon entry added, but only of title update
        # didn't result in the change thus triggering the listener
        await options_update_listener(hass, entry)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: GsAlarmConfigEntry
) -> bool:
    """
    Unloads the config entry.
    """
    _LOGGER.debug('Unloading platforms')
    unload_ok = all(
        await asyncio.gather(
            *(
                hass.config_entries.async_forward_entry_unload(
                    entry, platform
                )
                for platform in PLATFORMS
            )
        )
    )
    _LOGGER.debug(
        'Platforms unloaded %ssuccessfully', '' if unload_ok else 'un'
    )
    if unload_ok:
        await entry.runtime_data.client.close_notifications()
        _LOGGER.debug('Custom component unloaded')

    return unload_ok
