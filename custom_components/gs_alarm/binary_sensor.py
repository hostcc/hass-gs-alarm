from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
)

from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyg90alarm.entities.sensor import G90SensorTypes
from pyg90alarm.host_info import (G90HostInfoWifiStatus, G90HostInfoGsmStatus)
from .const import DOMAIN
import logging

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
    g90sensors = []
    for sensor in await hass.data[DOMAIN][entry.entry_id]['client'].sensors:
        if sensor.enabled:
            g90sensors.append(
                G90BinarySensor(sensor, hass.data[DOMAIN][entry.entry_id])
            )
    g90sensors.append(G90WifiStatusSensor(hass.data[DOMAIN][entry.entry_id]))
    g90sensors.append(G90GsmStatusSensor(hass.data[DOMAIN][entry.entry_id]))
    async_add_entities(g90sensors)


class G90BinarySensor(BinarySensorEntity):

    def __init__(self, sensor: object, hass_data: dict) -> None:
        self._sensor = sensor
        self._attr_unique_id = f"{hass_data['guid']}_sensor_{sensor.index}"
        self._attr_name = sensor.name
        hass_sensor_type = HASS_SENSOR_TYPES_MAPPING.get(sensor.type, None)
        if hass_sensor_type:
            self._attr_device_class = hass_sensor_type
        sensor.state_callback = self.state_callback
        self._attr_device_info = hass_data['device']
        self._hass_data = hass_data

    def state_callback(self, value):
        _LOGGER.debug(f'{self.unique_id}: Received state callback: {value}')
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        val = self._sensor.occupancy
        _LOGGER.debug(f'{self.unique_id}: Providing state {val}')
        return val


class G90WifiStatusSensor(BinarySensorEntity):

    def __init__(self, hass_data: dict) -> None:

        self._attr_name = 'WiFi Status'
        self._attr_unique_id = f"{hass_data['guid']}_sensor_wifi_status"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_device_info = hass_data['device']
        self._hass_data = hass_data

    @property
    def is_on(self) -> bool:
        # `host_info` of entry data is periodically updated by `G90AlarmPanel`
        status = self._hass_data['host_info'].wifi_status
        return status == G90HostInfoWifiStatus.OPERATIONAL


class G90GsmStatusSensor(BinarySensorEntity):

    def __init__(self, hass_data: dict) -> None:

        self._attr_name = 'GSM Status'
        self._attr_unique_id = f"{hass_data['guid']}_sensor_gsm_status"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_device_info = hass_data['device']
        self._hass_data = hass_data

    @property
    def is_on(self) -> bool:
        # See above re: how the data is updated
        status = self._hass_data['host_info'].gsm_status
        return status == G90HostInfoGsmStatus.OPERATIONAL
