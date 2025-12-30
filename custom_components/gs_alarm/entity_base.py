# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Base classes for common entities of `gs-alarm` integration.
"""
from __future__ import annotations
from typing import Any

from homeassistant.const import STATE_ON
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .mixin import GSAlarmGenerateIDsCommonMixin
from .coordinator import GsAlarmCoordinator


class GSAlarmEntityBase(
    CoordinatorEntity[GsAlarmCoordinator],
    GSAlarmGenerateIDsCommonMixin,
):
    """
    Base class for common entities of `gs-alarm` integration.

    Applicable to entities require only GUID in the unique/entity ID, and
    linked to parent device (one for alarm panel itself).

    :param coordinator: The coordinator to use.
    """
    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        # Generate unique ID and entity ID
        self._attr_unique_id = self.generate_unique_id(coordinator)
        self.entity_id = self.generate_entity_id(coordinator)
        # The entity is bound to the HASS device for the alarm panel itself
        self._attr_device_info = self.generate_parent_device_info(coordinator)


class GsAlarmSwitchRestoreEntityBase(
    SwitchEntity, GSAlarmEntityBase, RestoreEntity
):
    """
    Base class for switch entities of `gs-alarm` integration with state
    restoration support.

    An example of such entities are those not associated with specific panel
    sensors or devices.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=too-many-ancestors
    def __init__(
        self, coordinator: GsAlarmCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """
        Restores the last state on startup.
        """
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        self._attr_is_on = state is not None and state.state == STATE_ON

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """
        Store the switch ON state.
        """
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """
        Store the switch OFF state.
        """
        self._attr_is_on = False
        self.async_write_ha_state()
