"""
Sensors for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.util import slugify
from homeassistant.core import HomeAssistant

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
)

from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
if TYPE_CHECKING:
    from . import GsAlarmData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up a config entry."""
    g90sensors = [
        G90WifiSignal(hass.data[DOMAIN][entry.entry_id]),
        G90GsmSignal(hass.data[DOMAIN][entry.entry_id]),
        G90LastDevicePacket(hass.data[DOMAIN][entry.entry_id]),
        G90LastUpstreamPacket(hass.data[DOMAIN][entry.entry_id]),
    ]
    async_add_entities(g90sensors)


class G90BaseSensor(SensorEntity):
    """
    Base class for sensors.
    """
    # pylint:disable=too-few-public-methods
    def __init__(self, hass_data: GsAlarmData) -> None:
        self._hass_data = hass_data
        self._attr_device_info = hass_data.device
        self._attr_native_value = None
        self._attr_has_entity_name = True

    async def async_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor, required by base
        class.
        """
        _LOGGER.debug('Updating state')


class G90WifiSignal(G90BaseSensor):
    """
    Sensor for WiFi signal strength.
    """
    # pylint:disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self, hass_data: GsAlarmData) -> None:
        super().__init__(hass_data)
        self._attr_translation_key = 'wifi_signal'
        self._attr_unique_id = slugify(
            f"{self._hass_data.guid}_sensor_wifi_signal"
        )
        self._attr_icon = 'mdi:wifi'
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        await super().async_update()
        # `host_info` of entry data is periodically updated by `G90AlarmPanel`
        host_info = self._hass_data.host_info
        self._attr_native_value = host_info.wifi_signal_level


class G90GsmSignal(G90BaseSensor):
    """
    Sensor for GSM signal strength.
    """
    # pylint:disable=too-many-instance-attributes
    def __init__(self, hass_data: GsAlarmData) -> None:
        super().__init__(hass_data)
        self._attr_translation_key = 'gsm_signal'
        self._attr_unique_id = slugify(
            f"{self._hass_data.guid}_sensor_gsm_signal"
        )
        self._attr_icon = 'mdi:signal'
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        await super().async_update()
        # See above re: how the data is updated
        host_info = self._hass_data.host_info
        self._attr_native_value = host_info.gsm_signal_level


class G90LastDevicePacket(G90BaseSensor):
    """
    Sensor for last device packet.
    """
    def __init__(self, hass_data: GsAlarmData) -> None:
        super().__init__(hass_data)
        self._attr_translation_key = 'last_device_packet'
        self._attr_unique_id = slugify(
            f"{self._hass_data.guid}_sensor_last_device_packet"
        )
        self._attr_icon = 'mdi:clock-check'
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        await super().async_update()
        g90_client = self._hass_data.client
        self._attr_native_value = g90_client.last_device_packet_time


class G90LastUpstreamPacket(G90BaseSensor):
    """
    Sensor for last upstream packet.
    """
    def __init__(self, hass_data: GsAlarmData) -> None:
        super().__init__(hass_data)
        self._attr_translation_key = 'last_upstream_packet'
        self._attr_unique_id = slugify(
            f"{self._hass_data.guid}_sensor_last_upstream_packet"
        )
        self._attr_icon = 'mdi:cloud-clock'
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        await super().async_update()
        g90_client = self._hass_data.client
        self._attr_native_value = g90_client.last_upstream_packet_time
