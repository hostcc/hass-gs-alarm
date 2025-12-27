# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Buttons for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABCMeta, abstractmethod
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr
from homeassistant.const import EntityCategory, STATE_UNKNOWN
from homeassistant.components.button import ButtonEntity
from homeassistant.components.persistent_notification import (
    DOMAIN as NOTIFICATION_DOMAIN, ATTR_MESSAGE, ATTR_TITLE
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pyg90alarm import G90Device, G90Sensor, G90Error, G90TimeoutError

from .mixin import (
    GSAlarmGenerateIDsSensorMixin, GSAlarmGenerateIDsDeviceMixin,
)
from .entity_base import GSAlarmEntityBase
from .coordinator import GsAlarmCoordinator
from .binary_sensor import G90BinarySensor
from .switch import G90Switch
from .text import G90NewSensorName, G90NewDeviceName
from .select import G90NewSensorType, G90NewDeviceType
from .const import DOMAIN
from .utils import translate
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    def device_list_change_callback(device: G90Device, added: bool) -> None:
        # New relay is in the list, add button to delete it but only for
        # primary element (subindex 0) - important for multi-node devices
        if added and device.subindex == 0:
            async_add_entities([G90SwitchDelete(device, entry.runtime_data)])

    def sensor_list_change_callback(sensor: G90Sensor, added: bool) -> None:
        # New sensor is in the list, add button to delete it
        if added:
            async_add_entities([G90SensorDelete(sensor, entry.runtime_data)])

    # Register callbacks to add delete buttons when new devices/sensors are
    # added
    entry.runtime_data.client.device_list_change_callback.add(
        device_list_change_callback
    )
    entry.runtime_data.client.sensor_list_change_callback.add(
        sensor_list_change_callback
    )

    # Add buttons to register new sensors/relays
    async_add_entities([
        G90NewSensorRegister(entry.runtime_data),
        G90NewDeviceRegister(entry.runtime_data),
    ])


class G90EntityDeleteButtonBase(
    ButtonEntity, CoordinatorEntity[GsAlarmCoordinator],
    metaclass=ABCMeta
):
    """
    Base class for buttons to delete the sensor or relay from the alarm panel.

    :param g90_entity: The G90 entity (sensor or device) to be deleted.
    :param coordinator: The GS Alarm coordinator.
    """
    # pylint:disable=too-many-instance-attributes,abstract-method
    def __init__(
        self, g90_entity: G90Sensor | G90Device,
        coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._g90_entity = g90_entity
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = 'mdi:delete'
        self._attr_has_entity_name = True

    @property
    @abstractmethod
    def entity_kind(self) -> str:
        """
        The kind of entity being deleted (sensor or device).
        """

    async def async_press(self) -> None:
        """
        Delete the alarm entity.
        """
        try:
            _LOGGER.debug(
                "Deleting the %s '%s' with index %d, entity ID: %s",
                self.entity_kind, self.unique_id,
                self._g90_entity.index, self._g90_entity.extra_data
            )

            if not self.registry_entry or not self.registry_entry.device_id:
                raise ValueError(
                    f"Cannot delete {self.entity_kind} without a device ID"
                )

            # Delete the HASS device, will also remove all entities linked to
            # it
            dr.async_get(self.hass).async_remove_device(
                self.registry_entry.device_id
            )

            # Delete the entity from the alarm panel
            await self._g90_entity.delete()
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error deleting the %s '%s': %s",
                self.entity_kind, self.unique_id, repr(exc)
            )


class G90SwitchDelete(
    G90EntityDeleteButtonBase, GSAlarmGenerateIDsDeviceMixin
):
    """
    Button to delete the relay from the alarm panel.

    :param device: The G90 device to be deleted.
    :param coordinator: The GS Alarm coordinator.
    """
    # pylint:disable=too-many-instance-attributes,abstract-method
    # pylint:disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_switch_{device.index}_delete"
    ENTITY_ID_FMT = "{guid}_{device.name}_delete"

    def __init__(
        self, device: G90Device, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(device, coordinator)
        # Generate unique ID and entity ID
        self._attr_unique_id = self.generate_unique_id(coordinator, device)
        self.entity_id = self.generate_entity_id(coordinator, device)
        # The button is bound to the HASS device representing the relay
        self._attr_device_info = G90Switch.generate_device_info(
            coordinator, device
        )

        self._attr_translation_key = 'device_delete'
        self._attr_translation_placeholders = {
            'relay': device.protocol_data.parent_name,
        }

    @property
    def entity_kind(self) -> str:
        return 'device'


class G90SensorDelete(
    G90EntityDeleteButtonBase,
    GSAlarmGenerateIDsSensorMixin
):
    """
    Button to delete the sensor from the alarm panel.

    :param sensor: The G90 sensor to be deleted.
    :param coordinator: The GS Alarm coordinator.
    """
    # pylint:disable=too-many-instance-attributes,abstract-method
    # pylint:disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_{sensor.index}_delete"
    ENTITY_ID_FMT = "{guid}_{sensor.name}_delete"

    def __init__(
        self, sensor: G90Sensor, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(sensor, coordinator)
        # Generate unique ID and entity ID
        self._attr_unique_id = self.generate_unique_id(coordinator, sensor)
        self.entity_id = self.generate_entity_id(coordinator, sensor)
        # The button is bound to the HASS device representing the sensor
        self._attr_device_info = G90BinarySensor.generate_device_info(
            coordinator, sensor
        )

        self._attr_translation_key = 'sensor_delete'
        self._attr_translation_placeholders = {
            'sensor': sensor.name,
        }

    @property
    def entity_kind(self) -> str:
        return 'sensor'


class G90NewEntityRegisterButtonBase(
    ButtonEntity, GSAlarmEntityBase,
    metaclass=ABCMeta
):
    """
    Base class for button to register a new sensor/relay.

    :param coordinator: The GS Alarm coordinator.
    """
    # pylint:disable=abstract-method
    # pylint: disable=too-many-ancestors
    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = 'mdi:home-plus'
        self._attr_has_entity_name = True

    @property
    @abstractmethod
    def entity_kind(self) -> str:
        """
        The kind of entity being registered (sensor or device).
        """

    @abstractmethod
    def get_new_type_unique_id(self) -> str:
        """
        Get the unique ID of the HASS entity holding the new type.
        """

    @abstractmethod
    def get_new_name_unique_id(self) -> str:
        """
        Get the unique ID of the HASS entity holding the new name.
        """

    @abstractmethod
    async def register_entity(
        self, new_entity_type: str, new_entity_name: str
    ) -> G90Sensor | G90Device:
        """
        Register the new entity in the alarm panel.

        :param new_entity_type: The type of the new entity.
        :param new_entity_name: The name of the new entity.
        :return: The registered alarm panel entity.
        """

    async def async_press(self) -> None:
        """
        Handle the button press registering the new entity.
        """
        entity_registry = er.async_get(self.hass)

        # Retrieve new entity type from HASS entity (select)
        new_entity_type_id = entity_registry.async_get_entity_id(
            'select', DOMAIN, self.get_new_type_unique_id()
        )

        _LOGGER.debug(
            "Retrieving new %s type from %s",
            self.entity_kind, new_entity_type_id
        )
        new_entity_type = (
            self.hass.states.get(new_entity_type_id)
            if new_entity_type_id else None
        )

        # Entity type is mandatory, signal the error if not set
        if not new_entity_type or new_entity_type.state == STATE_UNKNOWN:
            _LOGGER.error(
                'New %s type is not set, cannot register a new %s',
                self.entity_kind, self.entity_kind
            )

            await self.hass.services.async_call(
                NOTIFICATION_DOMAIN,
                'create',
                {
                    ATTR_MESSAGE: translate(
                        self.hass, 'entity', (
                            'notifications'
                            f'.register_{self.entity_kind}_type_not_set'
                            '.name'
                        )
                    ),
                    ATTR_TITLE: self.coordinator.data.host_info.host_guid,
                },
                blocking=True,
            )
            return

        # Retrieve new entity name from HASS entity (text)
        new_entity_name_id = entity_registry.async_get_entity_id(
            'text', DOMAIN, self.get_new_name_unique_id()
        )

        _LOGGER.debug(
            'Retrieving new %s name from %s',
            self.entity_kind, new_entity_name_id
        )
        new_entity_name = (
            self.hass.states.get(new_entity_name_id)
            if new_entity_name_id else None
        )

        # Entity name is mandatory, signal the error if not set
        if not new_entity_name or new_entity_name.state == STATE_UNKNOWN:
            _LOGGER.error(
                'New %s name is not set, cannot register a new %s',
                self.entity_kind, self.entity_kind
            )

            await self.hass.services.async_call(
                NOTIFICATION_DOMAIN,
                'create',
                {
                    ATTR_MESSAGE: translate(
                        self.hass, 'entity', (
                            'notifications'
                            f'.register_{self.entity_kind}_name_not_set'
                            '.name'
                        )
                    ),
                    ATTR_TITLE: self.coordinator.data.host_info.host_guid,
                },
                blocking=True,
            )
            return

        # Attempt to register the new entity in the alarm panel
        registration_error = None
        new_entity = None
        try:
            _LOGGER.debug(
                "Registering a new %s, type='%s', name='%s'"
                " for the panel '%s'",
                self.entity_kind,
                new_entity_type.state, new_entity_name.state,
                self.coordinator.data.host_info.host_guid
            )

            # Create persistent notification about starting registration
            await self.hass.services.async_call(
                NOTIFICATION_DOMAIN,
                'create',
                {
                    ATTR_MESSAGE: translate(
                        self.hass, 'entity', (
                            'notifications'
                            f'.register_{self.entity_kind}_starting'
                            '.name'
                        ),
                        {
                            'type': new_entity_type.state,
                            'name': new_entity_name.state,
                        }
                    ),
                    ATTR_TITLE: self.coordinator.data.host_info.host_guid,
                },
                blocking=True,
            )

            # Register the new entity in the alarm panel
            new_entity = await self.register_entity(
                new_entity_type.state, new_entity_name.state
            )

            _LOGGER.debug(
                "New %s '%s', type='%s' with index %d registered successfully",
                self.entity_kind, new_entity.name,
                new_entity.type.name, new_entity.index
            )

        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error registering a new entity, type '%s', name='%s'"
                " for the panel '%s': %s",
                new_entity_type.state, new_entity_name.state,
                self.coordinator.data.host_info.host_guid, repr(exc)
            )
            registration_error = exc

        # Create persistent notification about registration result
        message_key = (
            'notifications'
            f'.register_{self.entity_kind}_finished'
            '.name'
        )
        message_placeholders = {
            'name': new_entity_name.state,
            'type': new_entity_type.state,
        }
        # Include error details if registration failed
        if registration_error:
            message_key = (
                'notifications'
                f'.register_{self.entity_kind}_error'
                '.name'
            )
            message_placeholders['error'] = str(registration_error)
        if new_entity:
            message_placeholders['index'] = str(new_entity.index)

        # Send notification about registration result
        await self.hass.services.async_call(
            NOTIFICATION_DOMAIN,
            'create',
            {
                ATTR_MESSAGE: translate(
                    self.hass, 'entity',
                    message_key, message_placeholders
                ),
                ATTR_TITLE: self.coordinator.data.host_info.host_guid,
            },
            blocking=True,
        )

        # Fire the HASS event about new entity registration
        self.coordinator.hass.bus.fire(
            f'{DOMAIN}_new_{self.entity_kind}_registration',
            {
                'guid': self.coordinator.data.host_info.host_guid,
                'name': new_entity_name.state,
                'type': new_entity_type.state,
                'index': new_entity.index if new_entity else None,
                'registered': new_entity is not None,
            }
        )


class G90NewSensorRegister(G90NewEntityRegisterButtonBase):
    """
    Button to register a new sensor in the alarm panel.
    """
    # pylint:disable=abstract-method
    # pylint:disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_new_sensor_register"
    ENTITY_ID_FMT = "{guid}_new_sensor_register"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'sensor_register'

    @property
    def entity_kind(self) -> str:
        return 'sensor'

    def get_new_type_unique_id(self) -> str:
        """
        Get the unique ID of the HASS entity holding the new sensor type.

        :return: The unique ID of the new sensor type entity.
        """
        return G90NewSensorType.generate_unique_id(self.coordinator)

    def get_new_name_unique_id(self) -> str:
        """
        Get the unique ID of the HASS entity holding the new sensor name.

        :return: The unique ID of the new sensor name entity.
        """
        return G90NewSensorName.generate_unique_id(self.coordinator)

    async def register_entity(
        self, new_entity_type: str, new_entity_name: str
    ) -> G90Sensor:
        """
        Register a new sensor in the alarm panel.

        :param new_entity_type: The type of the new sensor.
        :param new_entity_name: The name of the new sensor.
        :return: The registered sensor.
        """
        return await self.coordinator.client.register_sensor(
            new_entity_type, new_entity_name
        )


class G90NewDeviceRegister(G90NewEntityRegisterButtonBase):
    """
    Button to register a new relay in the alarm panel.
    """
    # pylint:disable=abstract-method
    # pylint:disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_new_device_register"
    ENTITY_ID_FMT = "{guid}_new_device_register"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'device_register'

    @property
    def entity_kind(self) -> str:
        return 'device'

    def get_new_type_unique_id(self) -> str:
        """
        Get the unique ID of the HASS entity holding the new relay type.

        :return: The unique ID of the new relay type entity.
        """
        return G90NewDeviceType.generate_unique_id(self.coordinator)

    def get_new_name_unique_id(self) -> str:
        """
        Get the unique ID of the HASS entity holding the new relay name.

        :return: The unique ID of the new relay name entity.
        """
        return G90NewDeviceName.generate_unique_id(self.coordinator)

    async def register_entity(
        self, new_entity_type: str, new_entity_name: str
    ) -> G90Device:
        """
        Register a new relay in the alarm panel.

        :param new_entity_type: The type of the new relay.
        :param new_entity_name: The name of the new relay.
        :return: The registered relay.
        """
        return await self.coordinator.client.register_device(
            new_entity_type, new_entity_name
        )
