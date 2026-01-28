# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Number entities for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity_base import G90HostConfigNumberField
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry


async def async_setup_entry(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    async_add_entities([
        G90HostConfigNumberField(
            entry.runtime_data,
            'alarm_siren_duration', 'mdi:bell', 's'
        ),
        G90HostConfigNumberField(
            entry.runtime_data,
            'arm_delay', 'mdi:timer', 's'
        ),
        G90HostConfigNumberField(
            entry.runtime_data,
            'alarm_delay', 'mdi:clock-alert', 's'
        ),
        G90HostConfigNumberField(
            entry.runtime_data,
            'backlight_duration', 'mdi:lightbulb', 's'
        ),
        G90HostConfigNumberField(
            entry.runtime_data,
            'ring_duration', 'mdi:phone-ring', 's'
        ),
        G90HostConfigNumberField(
            entry.runtime_data,
            'timezone_offset_m', 'mdi:map-clock', 'm'
        ),
    ])
