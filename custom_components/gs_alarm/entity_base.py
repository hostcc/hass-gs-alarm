# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Base classes for common entities of `gs-alarm` integration.
"""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

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
