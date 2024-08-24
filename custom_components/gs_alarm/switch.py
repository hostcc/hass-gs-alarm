"""
Switches for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import Any, Dict
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyg90alarm.entities.device import G90Device
from pyg90alarm.exceptions import (
    G90Error, G90TimeoutError
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    g90switches = []
    for device in (
        hass.data[DOMAIN][entry.entry_id]['panel_devices']
    ):
        g90switches.append(
            G90Switch(device, hass.data[DOMAIN][entry.entry_id])
        )

    async_add_entities(g90switches)


class G90Switch(SwitchEntity):
    # Not all base class methods are meaningfull in the context of the
    # integration, silence the `pylint` for those
    # pylint: disable=abstract-method
    """
    Switch specific to alarm panel.
    """
    def __init__(self, device: G90Device, hass_data: Dict[str, Any]) -> None:
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
        """
        Indicates if the switch is active (on).
        """
        return self._state

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """
        Turn on the switch.
        """
        try:
            await self._device.turn_on()
        except (G90Error, G90TimeoutError) as exc:
            # State isn't set to STATE_UNKNOWN since the panel doesn't support
            # reading it back
            _LOGGER.error(
                "Error turning on the switch '%s': %s",
                self.unique_id,
                repr(exc)
            )
        else:
            # State is only updated upon successful command execution
            self._state = True

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """
        Turn off the switch.
        """
        try:
            await self._device.turn_off()
        except (G90Error, G90TimeoutError) as exc:
            # See comment above
            _LOGGER.error(
                "Error turning off the switch '%s': %s",
                self.unique_id,
                repr(exc)
            )
        else:
            # See comment above
            self._state = False
