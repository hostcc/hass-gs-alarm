"""
tbd
"""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
)

from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up a config entry."""
    g90sensors = [
        G90WifiSignal(hass.data[DOMAIN][entry.entry_id]),
        G90GsmSignal(hass.data[DOMAIN][entry.entry_id]),
    ]
    async_add_entities(g90sensors)


# pylint:disable=too-few-public-methods
class G90BaseSensor(SensorEntity):
    """
    tbd
    """
    def __init__(self, hass_data: dict) -> None:
        self._hass_data = hass_data
        self._attr_device_info = hass_data['device']
        self._attr_native_value = None

    async def async_update(self):
        """
        tbd
        """
        _LOGGER.debug('Updating state')


# pylint:disable=too-few-public-methods
class G90WifiSignal(G90BaseSensor):
    """
    tbd
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attr_name = f'{DOMAIN}: WiFi Signal'
        self._attr_unique_id = f"{self._hass_data['guid']}_sensor_wifi_signal"
        self._attr_icon = 'mdi:wifi'
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_update(self):
        """
        tbd
        """
        await super().async_update()
        # `host_info` of entry data is periodically updated by `G90AlarmPanel`
        host_info = self._hass_data['host_info']
        self._attr_native_value = host_info.wifi_signal_level


class G90GsmSignal(G90BaseSensor):
    """
    tbd
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attr_name = f'{DOMAIN}: GSM Signal'
        self._attr_unique_id = f"{self._hass_data['guid']}_sensor_gsm_signal"
        self._attr_icon = 'mdi:signal'
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_update(self):
        """
        tbd
        """
        await super().async_update()
        # See above re: how the data is updated
        host_info = self._hass_data['host_info']
        self._attr_native_value = host_info.gsm_signal_level
