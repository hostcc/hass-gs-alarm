# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Text entities for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.components.text import TextEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import Event

from .const import DOMAIN
from .entity_base import (
    GSAlarmEntityBase, G90NetConfigTextField, G90AlarmPhonesTextField,
    G90SiaConfigTextField, G90CidConfigTextField,
)
from .coordinator import GsAlarmCoordinator
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry


async def async_setup_entry(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    coordinator = entry.runtime_data
    entities: list[Any] = [
        # Text entities for new sensor and relay names
        G90NewSensorName(coordinator),
        G90NewDeviceName(coordinator),
        # Add phone number entities
        G90AlarmPhonesTextField(
            coordinator,
            'panel_password', 'mdi:lock', True
        ),
        G90AlarmPhonesTextField(
            coordinator,
            'panel_phone_number', 'mdi:phone-settings', False
        ),
        G90AlarmPhonesTextField(
            coordinator,
            'phone_number_1', 'mdi:phone', False
        ),
        G90AlarmPhonesTextField(
            coordinator,
            'phone_number_2', 'mdi:phone', False
        ),
        G90AlarmPhonesTextField(
            coordinator,
            'phone_number_3', 'mdi:phone', False
        ),
        G90AlarmPhonesTextField(
            coordinator,
            'phone_number_4', 'mdi:phone', False
        ),
        G90AlarmPhonesTextField(
            coordinator,
            'phone_number_5', 'mdi:phone', False
        ),
        G90AlarmPhonesTextField(
            coordinator,
            'phone_number_6', 'mdi:phone', False
        ),
        G90AlarmPhonesTextField(
            coordinator,
            'sms_push_number_1', 'mdi:message-alert', False
        ),
        G90AlarmPhonesTextField(
            coordinator,
            'sms_push_number_2', 'mdi:message-alert', False
        ),
        # Add network config entities
        G90NetConfigTextField(
            coordinator,
            'ap_password', 'mdi:lock-check', True
        ),
        G90NetConfigTextField(
            coordinator,
            'apn_name', 'mdi:sim', False
        ),
        G90NetConfigTextField(
            coordinator,
            'apn_user', 'mdi:account', False
        ),
        G90NetConfigTextField(
            coordinator,
            'apn_password', 'mdi:lock-check', True
        ),
    ]
    if coordinator.data.sia_config is not None:
        entities.extend([
            G90SiaConfigTextField(
                coordinator, 'host', 'mdi:ip-network', False, 'sia_host'
            ),
            G90SiaConfigTextField(
                coordinator, 'account', 'mdi:identifier', False, 'sia_account'
            ),
            G90SiaConfigTextField(
                coordinator, 'receiver', 'mdi:phone', False, 'sia_receiver'
            ),
            G90SiaConfigTextField(
                coordinator, 'prefix', 'mdi:format-letter-case', False,
                'sia_prefix'
            ),
            G90SiaConfigTextField(
                coordinator, 'aes_key', 'mdi:key', True, 'sia_aes_key'
            ),
        ])
    if coordinator.data.cid_config is not None:
        entities.extend([
            G90CidConfigTextField(
                coordinator, 'phone1', 'mdi:phone', False, 'cid_phone1'
            ),
            G90CidConfigTextField(
                coordinator, 'phone2', 'mdi:phone', False, 'cid_phone2'
            ),
            G90CidConfigTextField(
                coordinator, 'user', 'mdi:account', False, 'cid_user'
            ),
        ])
    async_add_entities(entities)


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
