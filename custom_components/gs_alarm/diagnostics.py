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
    'panel_password', 'panel_phone_number', 'phone_number_1', 'phone_number_2',
    'phone_number_3', 'phone_number_4', 'phone_number_5', 'phone_number_6',
    'sms_push_number_1', 'sms_push_number_2', 'ap_password', 'apn_user',
    'apn_name', 'apn_password',
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

        alarm_panel_data = {
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
        }

        # Add configuration data if available
        try:
            host_config = await g90_client.host_config()
            if host_config:
                alarm_panel_data['host_config'] = host_config._asdict()
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.warning(
                "Unable to gather host_config for diagnostics: %s", repr(exc)
            )

        try:
            net_config = await g90_client.net_config()
            if net_config:
                alarm_panel_data['net_config'] = net_config._asdict()
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.warning(
                "Unable to gather net_config for diagnostics: %s", repr(exc)
            )

        try:
            alarm_phones = await g90_client.alarm_phones()
            if alarm_phones:
                alarm_panel_data['alarm_phones'] = alarm_phones._asdict()
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.warning(
                "Unable to gather alarm_phones for diagnostics: %s", repr(exc)
            )

        result = {
            'config_entry': entry.as_dict(),
            'device_entry': device.dict_repr if device else None,
            'alarm_panel': alarm_panel_data,
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
