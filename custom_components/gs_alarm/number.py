# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Number entities for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity_base import G90HostConfigNumberField, G90SiaConfigNumberField
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry


async def async_setup_entry(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    coordinator = entry.runtime_data
    entities: list[Any] = [
        G90HostConfigNumberField(
            coordinator,
            'alarm_siren_duration', 'mdi:bell', 's'
        ),
        G90HostConfigNumberField(
            coordinator,
            'arm_delay', 'mdi:timer', 's'
        ),
        G90HostConfigNumberField(
            coordinator,
            'alarm_delay', 'mdi:clock-alert', 's'
        ),
        G90HostConfigNumberField(
            coordinator,
            'backlight_duration', 'mdi:lightbulb', 's'
        ),
        G90HostConfigNumberField(
            coordinator,
            'ring_duration', 'mdi:phone-ring', 's'
        ),
        G90HostConfigNumberField(
            coordinator,
            'timezone_offset_m', 'mdi:map-clock', 'm'
        ),
    ]
    if coordinator.data.sia_config is not None:
        entities.extend([
            G90SiaConfigNumberField(
                coordinator, 'port', 'mdi:network-port', '',
                'sia_port'
            ),
            G90SiaConfigNumberField(
                coordinator, 'heartbeat_interval', 'mdi:heart-pulse', 's',
                'sia_heartbeat_interval'
            ),
        ])
    async_add_entities(entities)
