"""
The `gs_alarm` integration.
"""
from __future__ import annotations
from typing import List, Any, cast
from types import MappingProxyType
from dataclasses import dataclass
import asyncio
import logging

from pyg90alarm import (
    G90Alarm, G90Sensor, G90Device, G90HostInfo,
    G90Error, G90TimeoutError,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryNotReady, ConfigEntryError
)

from .const import (
    DOMAIN,
    CONF_IP_ADDR,
    CONF_SMS_ALERT_WHEN_ARMED,
    CONF_SIMULATE_ALERTS_FROM_HISTORY,
    CONF_DISABLED_SENSORS,
    CONF_NOTIFICATIONS_PROTOCOL,
    CONF_CLOUD_LOCAL_PORT,
    CONF_CLOUD_UPSTREAM_HOST,
    CONF_CLOUD_UPSTREAM_PORT,
    CONF_OPT_NOTIFICATIONS_LOCAL,
    CONF_OPT_NOTIFICATIONS_CLOUD,
    CONF_OPT_NOTIFICATIONS_CLOUD_UPSTREAM,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["alarm_control_panel", "switch", "binary_sensor", "sensor"]


@dataclass
class GsAlarmData:
    """
    tb
    """
    client: G90Alarm
    guid: str
    # Will periodically be updated by `G90AlarmPanel`
    host_info: G90HostInfo
    # Store panel sensors/devices for switch and sensor platforms
    panel_devices: List[G90Device]
    panel_sensors: List[G90Sensor]
    # HASS device information
    device: DeviceInfo


async def _options_enable_disable_sensors(
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

        cloud_upstream_host = options.get(CONF_CLOUD_UPSTREAM_HOST)
        cloud_upstream_port = options.get(CONF_CLOUD_UPSTREAM_PORT)

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
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """
    Handles options update.
    """
    try:
        g90_client = hass.data[DOMAIN][entry.entry_id].client
        _LOGGER.debug(
            'Updating alarm panel from config_entry options %s',
            entry.options
        )

        sms_alert_when_armed = entry.options.get(CONF_SMS_ALERT_WHEN_ARMED)
        # Skip updating the property if integration has no options persisted
        # (just added to HASS)
        if sms_alert_when_armed is not None:
            g90_client.sms_alert_when_armed = entry.options.get(
                CONF_SMS_ALERT_WHEN_ARMED, False
            )
            _LOGGER.debug(
                'G90Alarm.sms_alert_when_armed: %s',
                g90_client.sms_alert_when_armed
            )

        simulate_alerts_from_history = entry.options.get(
            CONF_SIMULATE_ALERTS_FROM_HISTORY
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
                    "Error %s simulate device alerts from history"
                    " for panel '%s': %s",
                    'enabling' if simulate_alerts_from_history
                    else 'disabling',
                    entry.title,
                    repr(exc)
                )

        disabled_sensors = entry.options.get(CONF_DISABLED_SENSORS)
        # See the comment above
        if disabled_sensors is not None:
            await _options_enable_disable_sensors(g90_client, disabled_sensors)

        # Configure the selected notifications protocol
        await _options_notifications_protocol(g90_client, entry.options)
    except G90TimeoutError as exc:
        raise ConfigEntryNotReady(
            f"Timeout while connecting to '{g90_client.host}'"
        ) from exc
    except G90Error as exc:
        raise ConfigEntryError(f"'{g90_client.host}': {repr(exc)}") from exc


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Sets up gs_alarm from a config entry.
    """
    hass.data.setdefault(DOMAIN, {})
    host = entry.data.get(CONF_IP_ADDR, None)
    try:
        g90_client = G90Alarm(host)
        host_info = await g90_client.get_host_info()
        devices = await g90_client.get_devices()
        sensors = await g90_client.get_sensors()
    except G90TimeoutError as exc:
        raise ConfigEntryNotReady(
            f"Timeout while connecting to '{host}'"
        ) from exc
    except G90Error as exc:
        raise ConfigEntryError(f"'{host}': {repr(exc)}") from exc

    hass.data[DOMAIN][entry.entry_id] = GsAlarmData(
        client=g90_client,
        guid=host_info.host_guid,
        # Will periodically be updated by `G90AlarmPanel`
        host_info=host_info,
        # Store panel sensors/devices for switch and sensor platforms
        panel_devices=devices,
        panel_sensors=sensors,
        # HASS device information
        device=DeviceInfo(
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
    )

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
        g90_client = hass.data[DOMAIN][entry.entry_id].client
        await g90_client.close_notifications()
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug('Custom component unloaded')

    return unload_ok
