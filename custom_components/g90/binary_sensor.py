from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_DOOR,
    DEVICE_CLASS_WINDOW,
    DEVICE_CLASS_GAS,
    DEVICE_CLASS_SMOKE,
    DEVICE_CLASS_PROBLEM,
    DEVICE_CLASS_VIBRATION,
    DEVICE_CLASS_MOISTURE,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_LOCK,
    DEVICE_CLASS_CONNECTIVITY,
    DEVICE_CLASS_COLD,
    DEVICE_CLASS_PLUG,
    DEVICE_CLASS_SOUND,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_OCCUPANCY,
)

from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyg90alarm.entities.sensor import G90SensorTypes
from .const import DOMAIN
import logging

HASS_SENSOR_TYPES_MAPPING = {
    G90SensorTypes.DOOR               : DEVICE_CLASS_DOOR,
    G90SensorTypes.GLASS              : DEVICE_CLASS_WINDOW,
    G90SensorTypes.GAS                : DEVICE_CLASS_GAS,
    G90SensorTypes.SMOKE              : DEVICE_CLASS_SMOKE,
    G90SensorTypes.SOS                : DEVICE_CLASS_PROBLEM,
    G90SensorTypes.VIB                : DEVICE_CLASS_VIBRATION,
    G90SensorTypes.WATER              : DEVICE_CLASS_MOISTURE,
    G90SensorTypes.INFRARED           : DEVICE_CLASS_MOTION,
    G90SensorTypes.IN_BEAM            : DEVICE_CLASS_MOTION,
    G90SensorTypes.REMOTE             : DEVICE_CLASS_LOCK,
    G90SensorTypes.RFID               : DEVICE_CLASS_LOCK,
    G90SensorTypes.DOORBELL           : DEVICE_CLASS_OCCUPANCY,
    G90SensorTypes.BUTTONID           : DEVICE_CLASS_LOCK,
    G90SensorTypes.WATCH              : DEVICE_CLASS_OCCUPANCY,
    G90SensorTypes.FINGER_LOCK        : DEVICE_CLASS_LOCK,
    G90SensorTypes.SUBHOST            : DEVICE_CLASS_CONNECTIVITY,
    G90SensorTypes.REMOTE_2_4G        : DEVICE_CLASS_LOCK,
    G90SensorTypes.CORD_SENSOR        : DEVICE_CLASS_MOTION,
    G90SensorTypes.SOCKET             : DEVICE_CLASS_PLUG,
    G90SensorTypes.SIREN              : DEVICE_CLASS_SOUND,
    G90SensorTypes.CURTAIN            : DEVICE_CLASS_WINDOW,
    G90SensorTypes.SLIDINGWIN         : DEVICE_CLASS_WINDOW,
    G90SensorTypes.AIRCON             : DEVICE_CLASS_COLD,
    G90SensorTypes.TV                 : DEVICE_CLASS_CONNECTIVITY,
    G90SensorTypes.SOCKET_2_4G        : DEVICE_CLASS_PLUG,
    G90SensorTypes.SIREN_2_4G         : DEVICE_CLASS_SOUND,
    G90SensorTypes.SWITCH_2_4G        : DEVICE_CLASS_POWER,
    G90SensorTypes.TOUCH_SWITCH_2_4G  : DEVICE_CLASS_POWER,
    G90SensorTypes.CURTAIN_2_4G       : DEVICE_CLASS_WINDOW,
    G90SensorTypes.CORD_DEV           : DEVICE_CLASS_MOTION,
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up a config entry."""
    g90_client = hass.data[DOMAIN][entry.entry_id]['client']
    g90_device = hass.data[DOMAIN][entry.entry_id]['device']
    g90_guid = hass.data[DOMAIN][entry.entry_id]['guid']
    g90sensors = []
    for sensor in await g90_client.sensors:
        if sensor.enabled:
            g90sensors.append(G90Sensor(sensor, g90_client, g90_device, g90_guid))
    async_add_entities(g90sensors)


class G90Sensor(BinarySensorEntity):

    def __init__(self, sensor: object, g90_client: object, g90_device: object, g90_guid: str) -> None:
        self._sensor = sensor
        self._g90_client = g90_client
        self._attr_unique_id = f'{g90_guid}_motion_{sensor.index}'
        self._attr_name = sensor.name
        hass_sensor_type = HASS_SENSOR_TYPES_MAPPING.get(sensor.type, None)
        if hass_sensor_type:
            self._attr_device_class = hass_sensor_type
        sensor.state_callback = self.state_callback
        self._attr_device_info = g90_device

    async def state_callback(self, value):
        _LOGGER.debug(f'{self.unique_id}: Received state callback: {value}')
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        val = self._sensor.occupancy
        _LOGGER.debug(f'{self.unique_id}: Providing state {val}')
        return val
