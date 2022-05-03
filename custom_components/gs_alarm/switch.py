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
    g90switches = []
    for device in await hass.data[DOMAIN][entry.entry_id]['client'].devices:
        g90switches.append(
            G90Switch(device, hass.data[DOMAIN][entry.entry_id])
        )
    async_add_entities(g90switches)


class G90Switch(SwitchEntity):

    def __init__(self, device: object, hass_data: dict) -> None:
        self._device = device
        self._state = False
        self._attr_unique_id = (
            f"{hass_data['guid']}_switch_{device.index}_{device.subindex + 1}"
        )
        self._attr_name = device.name
        self._attr_device_info = hass_data['device']
        self._hass_data = hass_data

    @property
    def is_on(self) -> bool:
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._device.turn_on()
        self._state = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._device.turn_off()
        self._state = False
