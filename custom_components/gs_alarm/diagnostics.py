# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Ilia Sotnikov
"""
Diagnostics support for the `gs-alarm` integration.
"""
from __future__ import annotations
from typing import Any, cast, TYPE_CHECKING
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.components.diagnostics.util import async_redact_data

from pyg90alarm import G90Error, G90TimeoutError

if TYPE_CHECKING:
    from . import GsAlarmConfigEntry

_LOGGER = logging.getLogger(__name__)
# Redact the properties could contain sensitive information
TO_REDACT = [
    'host_guid', 'host_phone_number', 'ip_addr', 'serial_number', 'name',
    'title', 'identifiers', 'extra_data', 'sensor_name', 'cloud_upstream_host',
]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: GsAlarmConfigEntry
) -> dict[str, Any]:
    """
    Returns diagnostics for the config entry.
    """
    return await async_get_device_diagnostics(
        hass, entry, cast(DeviceEntry, None)
    )


async def async_get_device_diagnostics(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """
    Returns diagnostics for the device entry.
    """

    try:
        g90_client = entry.runtime_data.client

        result = {
            'config_entry': entry.as_dict(),
            'device_entry': device.dict_repr if device else None,
            'alarm_panel': {
                'history': [
                    x._asdict()
                    # 50 history records should be the maximum for most of the
                    # panels
                    for x in await g90_client.history(count=50)
                ],
                'sensors': [
                    x._asdict()
                    for x in await g90_client.get_sensors()
                ],
                'devices': [
                    x._asdict()
                    for x in await g90_client.get_devices()
                ],
                'host_info': (await g90_client.get_host_info())._asdict(),
                'host_status': (await g90_client.get_host_status())._asdict(),
                'alert_config': repr(await g90_client.get_alert_config()),
            },
        }

        return cast(dict[str, Any], async_redact_data(result, TO_REDACT))
    # Errors raised by `pyg90alarm` are treated as non-terminating, just
    # resulting in error response
    except (G90Error, G90TimeoutError) as exc:
        msg = (
            "Unable to gather diagnostics data for"
            f" panel '{entry.title}': {repr(exc)}"
        )
        _LOGGER.error(msg)
        return {'error': msg}
