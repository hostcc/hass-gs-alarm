# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Text entities for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.components.text import TextEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import Event

from .const import DOMAIN
from .entity_base import GSAlarmEntityBase, G90ConfigTextField
from .coordinator import GsAlarmCoordinator
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry


async def async_setup_entry(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""

    async_add_entities([
        # Text entities for new sensor and relay names
        G90NewSensorName(entry.runtime_data),
        G90NewDeviceName(entry.runtime_data),
        # Add phone number entities
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.alarm_phones,
            'panel_password', 'mdi:lock', True
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.alarm_phones,
            'panel_phone_number', 'mdi:phone-settings', False
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.alarm_phones,
            'phone_number_1', 'mdi:phone', False
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.alarm_phones,
            'phone_number_2', 'mdi:phone', False
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.alarm_phones,
            'phone_number_3', 'mdi:phone', False
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.alarm_phones,
            'phone_number_4', 'mdi:phone', False
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.alarm_phones,
            'phone_number_5', 'mdi:phone', False
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.alarm_phones,
            'phone_number_6', 'mdi:phone', False
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.alarm_phones,
            'sms_push_number_1', 'mdi:message-alert', False
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.alarm_phones,
            'sms_push_number_2', 'mdi:message-alert', False
        ),
        # Add network config entities
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.net_config,
            'ap_password', 'mdi:lock-wireless', True
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.net_config,
            'apn_name', 'mdi:sim', False
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.net_config,
            'apn_user', 'mdi:account', False
        ),
        G90ConfigTextField(
            entry.runtime_data, entry.runtime_data.data.net_config,
            'apn_password', 'mdi:lock-check', True
        ),
    ])


class G90NewEntityTextBase(
    TextEntity, GSAlarmEntityBase,
):
    """
    Base class for text entity of new sensor/relay name.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors
    def __init__(
        self, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)

        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = 'mdi:pencil'
        self._attr_has_entity_name = True
        self._attr_native_value = ''

    async def async_set_value(self, value: str) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()

    async def handle_registration_event(self, event: Event) -> None:
        """
        Handle custom event to reset the text value.
        """
        # Ensure the event is for this panel
        if event.data['guid'] != self.coordinator.data.host_info.host_guid:
            return
        self._attr_native_value = ''
        self.async_write_ha_state()


class G90NewSensorName(G90NewEntityTextBase):
    """
    Text entity for new sensor name.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_new_sensor_name"
    ENTITY_ID_FMT = "{guid}_new_sensor_name"

    def __init__(
        self, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'new_sensor_name'

        # The text entity listens for registration events to reset its value
        self.coordinator.hass.bus.async_listen(
            f"{DOMAIN}_new_sensor_registration", self.handle_registration_event
        )


class G90NewDeviceName(G90NewEntityTextBase):
    """
    Text entity for new relay name.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_new_device_name"
    ENTITY_ID_FMT = "{guid}_new_device_name"

    def __init__(
        self, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'new_device_name'

        # The text entity listens for registration events to reset its value
        self.coordinator.hass.bus.async_listen(
            f"{DOMAIN}_new_device_registration", self.handle_registration_event
        )
