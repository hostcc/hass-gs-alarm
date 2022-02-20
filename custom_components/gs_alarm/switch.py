from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from typing import Any
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up a config entry."""
    g90_client = hass.data[DOMAIN][entry.entry_id]['client']
    g90_device = hass.data[DOMAIN][entry.entry_id]['device']
    g90_guid = hass.data[DOMAIN][entry.entry_id]['guid']
    g90switches = []
    for device in await g90_client.devices:
        g90switches.append(G90Switch(device, g90_device, g90_guid))
    async_add_entities(g90switches)


class G90Switch(SwitchEntity):

    def __init__(self, device: object, g90_device: object, g90_guid: str) -> None:
        self._device = device
        self._state = False
        self._attr_unique_id = f'{g90_guid}_switch_{device.index}_{device.subindex + 1}'
        self._attr_name = device.name
        self._attr_device_info = g90_device

    @property
    def is_on(self) -> bool:
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._device.turn_on()
        self._state = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._device.turn_off()
        self._state = False
