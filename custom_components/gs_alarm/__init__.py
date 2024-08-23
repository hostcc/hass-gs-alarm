"""
The `gs_alarm` integration.
"""
from __future__ import annotations
from typing import List
import asyncio
import logging

from pyg90alarm import G90Alarm
from pyg90alarm.exceptions import (
    G90Error, G90TimeoutError
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryNotReady, ConfigEntryError
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["alarm_control_panel", "switch", "binary_sensor", "sensor"]


async def _enable_disable_sensors(
    g90_client: G90Alarm, disabled_sensors: List[str]
) -> None:
    """
    Perform enabling/disabling sensors support that during options (configure)
    flow
    """
    _LOGGER.debug('Sensors to disable: %s', disabled_sensors)
    for sensor in await g90_client.get_sensors():
        # Ensure no attempts made to disable sensors not supporting that
        if not sensor.supports_enable_disable:
            continue
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


async def options_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """
    Handles options update.
    """
    g90_client = hass.data[DOMAIN][entry.entry_id]['client']
    _LOGGER.debug(
        'Updating alarm panel from config_entry options %s',
        entry.options
    )

    sms_alert_when_armed = entry.options.get('sms_alert_when_armed')
    # Skip updating the property if integration has no options persisted (just
    # added to HASS)
    if sms_alert_when_armed is not None:
        g90_client.sms_alert_when_armed = entry.options.get(
            'sms_alert_when_armed', False
        )
        _LOGGER.debug(
            'G90Alarm.sms_alert_when_armed: %s',
            g90_client.sms_alert_when_armed
        )

    simulate_alerts_from_history = entry.options.get(
        'simulate_alerts_from_history'
    )
    # See the comment above
    if simulate_alerts_from_history is not None:
        try:
            if simulate_alerts_from_history:
                _LOGGER.debug(
                    'Starting to simulate device alerts from history'
                )
                await g90_client.start_simulating_alerts_from_history()
            else:
                _LOGGER.debug(
                    'Stopping to simulate device alerts from history'
                )
                await g90_client.stop_simulating_alerts_from_history()
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                'Error %s simulate device alerts from history: %s',
                'enabling' if simulate_alerts_from_history else 'disabling',
                repr(exc)
            )

    disabled_sensors = entry.options.get('disabled_sensors')
    # See the comment above
    if disabled_sensors is not None:
        await _enable_disable_sensors(g90_client, disabled_sensors)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Sets up gs_alarm from a config entry.
    """
    hass.data.setdefault(DOMAIN, {})
    host = entry.data.get('ip_addr', None)
    try:
        g90_client = G90Alarm(host)
        host_info = await g90_client.get_host_info()
        devices = await g90_client.get_devices()
        sensors = await g90_client.get_sensors()
        await g90_client.listen_device_notifications()
    except G90TimeoutError as exc:
        raise ConfigEntryNotReady(
            f"Timeout while connecting to '{host}'"
        ) from exc
    except G90Error as exc:
        raise ConfigEntryError(f"'{host}': {repr(exc)}") from exc

    hass.data[DOMAIN][entry.entry_id] = {
        'client': g90_client,
        'guid': host_info.host_guid,
        # Will periodically be updated by `G90AlarmPanel`
        'host_info': host_info,
        # Store panel sensors/devices for switch and sensor platforms
        'panel_devices': devices,
        'panel_sensors': sensors,
        # HASS device information
        'device': DeviceInfo(
            identifiers={
                (DOMAIN, host_info.host_guid)
            },
            manufacturer='Golden Security',
            model=host_info.product_name,
            name=host_info.host_guid,
            serial_number=host_info.host_guid,
            sw_version=f'MCU: {host_info.mcu_hw_version},'
                       f' WiFi: {host_info.wifi_hw_version}',
        )
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    # Update the entry's title
    if not hass.config_entries.async_update_entry(
        entry, title=host_info.host_guid
    ):
        # Force setting options upon entry added, but only of title update
        # didn't result in the change thus triggering the listener
        await options_update_listener(hass, entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
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
        'Platforms unloaded %successfully', '' if unload_ok else 'un'
    )
    if unload_ok:
        g90_client = hass.data[DOMAIN][entry.entry_id]['client']
        g90_client.close_device_notifications()
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug('Custom component unloaded')

    return unload_ok
