"""
Binary sensors for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import Dict, Any, cast, List
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)

from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyg90alarm.entities.sensor import (G90Sensor, G90SensorTypes)
from pyg90alarm.host_info import (G90HostInfoWifiStatus, G90HostInfoGsmStatus)
from .const import DOMAIN

HASS_SENSOR_TYPES_MAPPING = {
    G90SensorTypes.DOOR: BinarySensorDeviceClass.DOOR,
    G90SensorTypes.GLASS: BinarySensorDeviceClass.WINDOW,
    G90SensorTypes.GAS: BinarySensorDeviceClass.GAS,
    G90SensorTypes.SMOKE: BinarySensorDeviceClass.SMOKE,
    G90SensorTypes.SOS: BinarySensorDeviceClass.PROBLEM,
    G90SensorTypes.VIB: BinarySensorDeviceClass.VIBRATION,
    G90SensorTypes.WATER: BinarySensorDeviceClass.MOISTURE,
    G90SensorTypes.INFRARED: BinarySensorDeviceClass.MOTION,
    G90SensorTypes.IN_BEAM: BinarySensorDeviceClass.MOTION,
    G90SensorTypes.REMOTE: BinarySensorDeviceClass.LOCK,
    G90SensorTypes.RFID: BinarySensorDeviceClass.LOCK,
    G90SensorTypes.DOORBELL: BinarySensorDeviceClass.OCCUPANCY,
    G90SensorTypes.BUTTONID: BinarySensorDeviceClass.LOCK,
    G90SensorTypes.WATCH: BinarySensorDeviceClass.OCCUPANCY,
    G90SensorTypes.FINGER_LOCK: BinarySensorDeviceClass.LOCK,
    G90SensorTypes.SUBHOST: BinarySensorDeviceClass.CONNECTIVITY,
    G90SensorTypes.REMOTE_2_4G: BinarySensorDeviceClass.LOCK,
    G90SensorTypes.CORD_SENSOR: BinarySensorDeviceClass.MOTION,
    G90SensorTypes.SOCKET: BinarySensorDeviceClass.PLUG,
    G90SensorTypes.SIREN: BinarySensorDeviceClass.SOUND,
    G90SensorTypes.CURTAIN: BinarySensorDeviceClass.WINDOW,
    G90SensorTypes.SLIDINGWIN: BinarySensorDeviceClass.WINDOW,
    G90SensorTypes.AIRCON: BinarySensorDeviceClass.COLD,
    G90SensorTypes.TV: BinarySensorDeviceClass.CONNECTIVITY,
    G90SensorTypes.SOCKET_2_4G: BinarySensorDeviceClass.PLUG,
    G90SensorTypes.SIREN_2_4G: BinarySensorDeviceClass.SOUND,
    G90SensorTypes.SWITCH_2_4G: BinarySensorDeviceClass.POWER,
    G90SensorTypes.TOUCH_SWITCH_2_4G: BinarySensorDeviceClass.POWER,
    G90SensorTypes.CURTAIN_2_4G: BinarySensorDeviceClass.WINDOW,
    G90SensorTypes.CORD_DEV: BinarySensorDeviceClass.MOTION,
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up a config entry."""
    g90sensors: List[
        G90WifiStatusSensor | G90GsmStatusSensor | G90BinarySensor
    ] = []
    for sensor in (
        await hass.data[DOMAIN][entry.entry_id]['client'].get_sensors()
    ):
        if sensor.enabled:
            g90sensors.append(
                G90BinarySensor(sensor, hass.data[DOMAIN][entry.entry_id])
            )
    g90sensors.append(G90WifiStatusSensor(hass.data[DOMAIN][entry.entry_id]))
    g90sensors.append(G90GsmStatusSensor(hass.data[DOMAIN][entry.entry_id]))
    async_add_entities(g90sensors)


class G90BinarySensor(BinarySensorEntity):
    """
    Binary sensor specific to alarm panel.
    """
    def __init__(
        self, g90_sensor: G90Sensor, hass_data: Dict[str, Any]
    ) -> None:
        self._g90_sensor = g90_sensor
        self._attr_unique_id = f"{hass_data['guid']}_sensor_{g90_sensor.index}"
        self._attr_name = g90_sensor.name
        hass_sensor_type = HASS_SENSOR_TYPES_MAPPING.get(g90_sensor.type, None)
        if hass_sensor_type:
            self._attr_device_class = hass_sensor_type
        g90_sensor.state_callback = self.state_callback
        self._attr_device_info = hass_data['device']
        self._hass_data = hass_data

    async def async_added_to_hass(self) -> None:
        """
        Invoked by HASS when entity is added.
        """
        # Store the entity ID as extra data to `G90Sensor` instance, it will be
        # provided in the arguments when `G90Alarm.alarm_callback` is invoked
        _LOGGER.debug(
            'Storing entity ID as extra data: sensor %s (idx %s), ID: %s',
            self._g90_sensor.name, self._g90_sensor.index, self.entity_id
        )
        self._g90_sensor.extra_data = self.entity_id

    def state_callback(self, value: bool) -> None:
        """
        Invoked by `pyg90alarm` when its sensor changes the state.
        """
        _LOGGER.debug('%s: Received state callback: %s', self.unique_id, value)
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        """
        Indicates if sensor is active.
        """
        val: bool = self._g90_sensor.occupancy
        _LOGGER.debug('%s: Providing state %s', self.unique_id, val)
        return val


# pylint:disable=too-few-public-methods
class G90WifiStatusSensor(BinarySensorEntity):
    """
    WiFi status sensor.
    """
    def __init__(self, hass_data: Dict[str, Any]) -> None:
        self._attr_name = f'{DOMAIN}: WiFi Status'
        self._attr_unique_id = f"{hass_data['guid']}_sensor_wifi_status"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = hass_data['device']
        self._hass_data = hass_data

    @property
    def is_on(self) -> bool:
        """
        Indicates if WiFi is connected.
        """
        # `host_info` of entry data is periodically updated by `G90AlarmPanel`
        status = self._hass_data['host_info'].wifi_status
        return cast(bool, status == G90HostInfoWifiStatus.OPERATIONAL)


# pylint:disable=too-few-public-methods
class G90GsmStatusSensor(BinarySensorEntity):
    """
    GSM status sensor.
    """
    def __init__(self, hass_data: Dict[str, Any]) -> None:
        self._attr_name = f'{DOMAIN}: GSM Status'
        self._attr_unique_id = f"{hass_data['guid']}_sensor_gsm_status"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = hass_data['device']
        self._hass_data = hass_data

    @property
    def is_on(self) -> bool:
        """
        Indicates if GSM is connected.
        """
        # See above re: how the data is updated
        status = self._hass_data['host_info'].gsm_status
        return cast(bool, status == G90HostInfoGsmStatus.OPERATIONAL)
