# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Text entities for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
import logging
from abc import ABC, abstractmethod

from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.components.text import TextEntity
from homeassistant.components.text.const import DOMAIN as TEXT_DOMAIN
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import Event
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import device_registry as dr

from pyg90alarm import G90Device, G90Sensor, G90Error, G90TimeoutError

from .const import DOMAIN
from .entity_base import (
    GSAlarmEntityBase, G90NetConfigTextField, G90AlarmPhonesTextField,
    G90SiaConfigTextField, G90CidConfigTextField,
)
from .coordinator import GsAlarmCoordinator
from .mixin import GSAlarmGenerateIDsSensorMixin, GSAlarmGenerateIDsDeviceMixin
from .binary_sensor import G90BinarySensor
from .switch import G90Switch
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    def device_list_change_callback(device: G90Device, added: bool) -> None:
        # Add rename text entity for new device if it is the primary element
        if added and device.subindex == 0:
            async_add_entities([G90DeviceName(device, coordinator)])

    def sensor_list_change_callback(sensor: G90Sensor, added: bool) -> None:
        # Similarly, but for sensors
        if added and sensor.supports_updates:
            async_add_entities([G90SensorName(sensor, coordinator)])

    coordinator = entry.runtime_data
    # Register callback to add rename text entities for new sensors/devices
    entry.runtime_data.client.device_list_change_callback.add(
        device_list_change_callback
    )
    entry.runtime_data.client.sensor_list_change_callback.add(
        sensor_list_change_callback
    )

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
    ENTITY_DOMAIN = TEXT_DOMAIN

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


class G90RenameTextEntityBase(
    TextEntity,
    CoordinatorEntity[GsAlarmCoordinator],
    ABC
):
    """
    Base class for sensor/device rename text entities.
    """
    # pylint: disable=too-many-ancestors,too-many-instance-attributes
    ENTITY_DOMAIN: Optional[str] = TEXT_DOMAIN

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = 'mdi:pencil'
        self._attr_has_entity_name = True

    @property
    @abstractmethod
    def entity_kind(self) -> str:
        """
        Kind of panel entity being renamed.
        """

    @property
    @abstractmethod
    def panel_name(self) -> str:
        """
        Current name as known to alarm panel.
        """

    @abstractmethod
    async def set_panel_name(self, value: str) -> None:
        """
        Rename entity on alarm panel.
        """

    async def async_set_value(self, value: str) -> None:
        """
        Set value and apply rename on panel immediately.
        """
        # Ignore empty or whitespace-only names
        if not value or value.isspace():
            _LOGGER.debug(
                "Empty %s name supplied for '%s', rename is ignored",
                self.entity_kind, self.unique_id
            )
            return

        # Rename the entity on the panel
        try:
            await self.set_panel_name(value)
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error renaming %s '%s' to '%s': %s",
                self.entity_kind,
                self.unique_id,
                value,
                repr(exc)
            )
            return
        _LOGGER.debug(
            "Renamed %s '%s' to '%s'",
            self.entity_kind, self.unique_id, value
        )

        self._attr_native_value = value

        if self.registry_entry and self.registry_entry.device_id:
            # Update device name immediately in device registry.
            # This should be updated during config entry reload below,
            # but we do it here for immediate visibility.
            dr.async_get(self.hass).async_update_device(
                self.registry_entry.device_id,
                name=value
            )

        # Request data update from panel to reflect the new name
        await self.coordinator.async_request_refresh()

        # Ideally, this should only reload entities for the renamed
        # sensor/device, but the entity registry caches original_name
        # when entities are first registered. The only reliable way to
        # update this cache is to reload the integration, which removes
        # and re-adds all entities with fresh naming metadata.
        # This causes brief unavailability of all integration
        # entities, but ensures the name change is reflected.
        if self.coordinator.config_entry:
            self.coordinator.hass.config_entries.async_schedule_reload(
                self.coordinator.config_entry.entry_id
            )

        self.async_write_ha_state()

    @property
    def native_value(self) -> str:
        return self.panel_name


class G90SensorName(
    G90RenameTextEntityBase,
    GSAlarmGenerateIDsSensorMixin
):
    """
    Text entity to rename panel sensor.
    """
    # pylint: disable=too-many-ancestors
    UNIQUE_ID_FMT = "{guid}_sensor_{sensor.index}_panel_name"
    ENTITY_ID_FMT = "{guid}_{sensor.name}_panel_name"

    def __init__(
        self, sensor: G90Sensor, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._sensor = sensor
        self._attr_unique_id = self.generate_unique_id(coordinator, sensor)
        self.entity_id = self.generate_entity_id(coordinator, sensor)
        # The text entity is bound to the HASS device representing the sensor
        self._attr_device_info = G90BinarySensor.generate_device_info(
            coordinator, sensor
        )

        self._attr_translation_key = 'sensor_panel_name'
        self._attr_native_value = sensor.name

    @property
    def entity_kind(self) -> str:
        return 'sensor'

    @property
    def panel_name(self) -> str:
        return self._sensor.name

    async def set_panel_name(self, value: str) -> None:
        await self._sensor.set_name(value)


class G90DeviceName(
    G90RenameTextEntityBase,
    GSAlarmGenerateIDsDeviceMixin
):
    """
    Text entity to rename panel relay.
    """
    # pylint: disable=too-many-ancestors
    UNIQUE_ID_FMT = "{guid}_switch_{device.index}_panel_name"
    ENTITY_ID_FMT = "{guid}_{device.name}_panel_name"

    def __init__(
        self, device: G90Device, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = self.generate_unique_id(coordinator, device)
        self.entity_id = self.generate_entity_id(coordinator, device)
        # The text entity is bound to the HASS device representing the relay
        self._attr_device_info = G90Switch.generate_device_info(
            coordinator, device
        )

        self._attr_translation_key = 'device_panel_name'
        self._attr_native_value = device.name

    @property
    def entity_kind(self) -> str:
        return 'device'

    @property
    def panel_name(self) -> str:
        return self._device.name

    async def set_panel_name(self, value: str) -> None:
        await self._device.set_name(value)
