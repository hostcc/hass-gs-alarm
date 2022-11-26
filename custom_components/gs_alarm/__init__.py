"""
The `gs_alarm` integration.
"""
from __future__ import annotations
import asyncio
import logging

from pyg90alarm import G90Alarm
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["alarm_control_panel", "switch", "binary_sensor", "sensor"]


async def _enable_disable_sensors(g90_client, disabled_sensors):
    """
    Perform enabling/disabling sensors support that during options (configure)
    flow
    """
    for sensor in await g90_client.get_sensors():
        # Calculate target state for the sensor, depending on whether it has
        # been included into `disabled_sensors` configure result or not
        enable_sensor = (
            str(sensor.index) not in disabled_sensors
        )
        # Skip changing the sensor if already in target state
        if sensor.enabled == enable_sensor:
            _LOGGER.debug(
                'Not changing state for sensor idx=%s name=%s,'
                ' already in target state (enabled=%s)',
                sensor.index, sensor.name, enable_sensor
            )
            continue

        # Update the state of the sensor
        _LOGGER.debug(
            'Changing state of sensor idx=%s name=%s to %s',
            sensor.index, sensor.name,
            'enabled' if enable_sensor else 'disabled'
        )
        await sensor.set_enabled(enable_sensor)


async def options_update_listener(hass, entry):
    """
    Handles options update.
    """
    g90_client = hass.data[DOMAIN][entry.entry_id]['client']
    g90_client.sms_alert_when_armed = entry.options['sms_alert_when_armed']
    await _enable_disable_sensors(
        g90_client, entry.options['disabled_sensors']
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Sets up gs_alarm from a config entry.
    """
    hass.data.setdefault(DOMAIN, {})
    g90_client = G90Alarm(host=entry.data.get('ip_addr', None))
    host_info = await g90_client.get_host_info()

    hass.data[DOMAIN][entry.entry_id] = {
        'client': g90_client,
        'guid': host_info.host_guid,
        # Will periodically be updated by `G90AlarmPanel`
        'host_info': host_info,
        'device': {
            'name': f'{DOMAIN}:{host_info.host_guid}',
            'model': host_info.product_name,
            'sw_version': f'MCU: {host_info.mcu_hw_version},'
                          f' WiFi: {host_info.wifi_hw_version}',
            'identifiers': {
                (DOMAIN, host_info.host_guid)
            },
            'manufacturer': 'Golden Security',
        }
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await g90_client.listen_device_notifications()

    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unloads the config entry.
    """
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
    _LOGGER.debug('Platforms unloaded')
    if unload_ok:
        g90_client = hass.data[DOMAIN][entry.entry_id]['client']
        g90_client.close_device_notifications()
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug('Custom component unloaded')

    return unload_ok
