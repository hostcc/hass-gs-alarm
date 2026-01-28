# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Number entities for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity_base import G90ConfigNumberField
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry


async def async_setup_entry(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    async_add_entities([
        G90ConfigNumberField(
            entry.runtime_data,
            entry.runtime_data.data.get_host_config_func,
            'alarm_siren_duration', 'mdi:bell', 's'
        ),
        G90ConfigNumberField(
            entry.runtime_data,
            entry.runtime_data.data.get_host_config_func,
            'arm_delay', 'mdi:timer', 's'
        ),
        G90ConfigNumberField(
            entry.runtime_data,
            entry.runtime_data.data.get_host_config_func,
            'alarm_delay', 'mdi:clock-alert', 's'
        ),
        G90ConfigNumberField(
            entry.runtime_data,
            entry.runtime_data.data.get_host_config_func,
            'backlight_duration', 'mdi:lightbulb', 's'
        ),
        G90ConfigNumberField(
            entry.runtime_data,
            entry.runtime_data.data.get_host_config_func,
            'ring_duration', 'mdi:phone-ring', 's'
        ),
        G90ConfigNumberField(
            entry.runtime_data,
            entry.runtime_data.data.get_host_config_func,
            'timezone_offset_m', 'mdi:map-clock', 'm'
        ),
    ])
