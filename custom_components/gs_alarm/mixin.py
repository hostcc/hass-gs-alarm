# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Mixin classes for `gs-alarm` integration.
"""
from __future__ import annotations
from typing import Optional, Any, Dict
from abc import ABC, abstractmethod

from homeassistant.util import slugify
from homeassistant.helpers.device_registry import DeviceInfo

from pyg90alarm import G90Sensor, G90Device

from .const import DOMAIN, MANUFACTURER
from .coordinator import GsAlarmCoordinator


class GSAlarmGenerateIDsMixinBase(ABC):
    # pylint: disable=too-few-public-methods
    """
    Base mixin class that defines the interface and shared helpers for
    generating unique IDs and entity IDs for integration entities.

    Subclasses are expected to:
    - Provide format strings via ``UNIQUE_ID_FMT`` and ``ENTITY_ID_FMT``.
    - Implement :meth:`generate_unique_id` and :meth:`generate_entity_id`
      to construct IDs for specific entity types, typically using the
      coordinator data and object-specific placeholders.
    """
    UNIQUE_ID_FMT: Optional[str] = None
    ENTITY_ID_FMT: Optional[str] = None

    @classmethod
    @abstractmethod
    def generate_unique_id(
        cls, coordinator: GsAlarmCoordinator,
        obj: Any
    ) -> str:
        """
        Generate unique ID for the entity.

        :param coordinator: The coordinator to use.
        :param obj: The object (sensor, device, etc.) to use.
        :return: The generated unique ID.
        """

    @classmethod
    @abstractmethod
    def generate_entity_id(
        cls, coordinator: GsAlarmCoordinator,
        obj: Any
    ) -> str:
        """
        Generate entity ID for the entity.

        :param coordinator: The coordinator to use.
        :param obj: The object (sensor, device, etc.) to use.
        :return: The generated entity ID.
        """

    @classmethod
    def generate_unique_id_with_placeholders(
        cls, coordinator: GsAlarmCoordinator,
        placeholders: Dict[str, Any]
    ) -> str:
        """
        Generate unique ID for the entity using provided placeholders.

        :param coordinator: The coordinator to use.
        :param placeholders: A dictionary of placeholders to format
            the unique ID.
        :return: The generated unique ID.
        """
        if not cls.UNIQUE_ID_FMT:
            raise NotImplementedError("UNIQUE_ID_FMT is not defined")

        return slugify(
            cls.UNIQUE_ID_FMT.format(
                guid=coordinator.data.host_info.host_guid, **placeholders
            )
        )

    @classmethod
    def generate_entity_id_with_placeholders(
        cls, coordinator: GsAlarmCoordinator,
        placeholders: Dict[str, Any]
    ) -> str:
        """
        Generate entity ID for the entity using provided placeholders.

        :param coordinator: The coordinator to use.
        :param placeholders: A dictionary of placeholders to format
            the entity ID.
        :return: The generated entity ID.
        """
        if not cls.ENTITY_ID_FMT:
            raise NotImplementedError("ENTITY_ID_FMT is not defined")

        # Formally, the entity ID should have first component being the
        # platform name (e.g. `swoitch.`, `sensor.` etc), but practically any
        # content there works, HASS seems properly parsing it out and replacing
        # it with platform name as needed.
        return f'{DOMAIN}.{slugify(
            cls.ENTITY_ID_FMT.format(
                guid=coordinator.data.host_info.host_guid, **placeholders
            )
        )}'

    @classmethod
    def generate_parent_device_info(
        cls, coordinator: GsAlarmCoordinator
    ) -> DeviceInfo:
        """
        Generate DeviceInfo for the parent HASS device, typically associated
        with the alarm panel itself.

        :param coordinator: The coordinator to use.
        :return: The generated DeviceInfo.
        """
        if not coordinator.data.host_info:
            raise ValueError("Coordinator host info is not set")

        return DeviceInfo(
            identifiers={
                (DOMAIN, coordinator.data.host_info.host_guid)
            },
            manufacturer=MANUFACTURER,
            name=coordinator.data.host_info.host_guid,
            serial_number=coordinator.data.host_info.host_guid,
            model=coordinator.data.host_info.product_name,
            sw_version=(
                f'MCU: {coordinator.data.host_info.mcu_hw_version},'
                f' WiFi: {coordinator.data.host_info.wifi_hw_version}'
            ),
        )


class GSAlarmGenerateIDsCommonMixin(GSAlarmGenerateIDsMixinBase):
    """
    Mixin to generate IDs for common entities not tied to sensors or devices.
    """

    @classmethod
    def generate_unique_id(
        cls, coordinator: GsAlarmCoordinator, obj: Any = None
    ) -> str:
        """
        Generate unique ID for the entity.

        :param coordinator: The coordinator to use.
        :param obj: unused, kept for interface consistency.
        :return: The generated unique ID.
        """
        return super().generate_unique_id_with_placeholders(
            coordinator, {}
        )

    @classmethod
    def generate_entity_id(
        cls, coordinator: GsAlarmCoordinator, obj: Any = None
    ) -> str:
        """
        Generate entity ID for the entity.

        :param coordinator: The coordinator to use.
        :param obj: unused, kept for interface consistency.
        :return: The generated entity ID.
        """
        return super().generate_entity_id_with_placeholders(
            coordinator, {}
        )


class GSAlarmGenerateIDsSensorMixin(GSAlarmGenerateIDsMixinBase):
    """
    Mixin to generate IDs for sensor entities.

    Exposes `G90Sensor` object as `sensor` placeholder for the format strings.
    """

    @classmethod
    def generate_unique_id(
        cls, coordinator: GsAlarmCoordinator, obj: G90Sensor
    ) -> str:
        """
        Generate unique ID for the sensor.

        :param coordinator: The coordinator to use.
        :param obj: The sensor object to use.
        :return: The generated unique ID.
        """
        return super().generate_unique_id_with_placeholders(
            coordinator, {'sensor': obj}
        )

    @classmethod
    def generate_entity_id(
        cls, coordinator: GsAlarmCoordinator,
        obj: G90Sensor,
    ) -> str:
        """
        Generate entity ID for the sensor.

        :param coordinator: The coordinator to use.
        :param obj: The sensor object to use.
        :return: The generated entity ID.
        """
        return super().generate_entity_id_with_placeholders(
            coordinator, {'sensor': obj}
        )

    @classmethod
    def generate_device_info(
        cls, coordinator: GsAlarmCoordinator, obj: G90Sensor
    ) -> DeviceInfo:
        """
        Generate DeviceInfo for the sensor, will be linked via the paren
        HASS device.

        :param coordinator: The coordinator to use.
        :param obj: The sensor object to use.
        :return: The generated DeviceInfo.
        """
        if not coordinator.data.host_info:
            raise ValueError("Coordinator host info is not set")

        return DeviceInfo(
            manufacturer=MANUFACTURER,
            model=obj.type_name or '',
            name=obj.name,
            serial_number=coordinator.data.host_info.host_guid,
            identifiers={
                (DOMAIN, cls.generate_unique_id(coordinator, obj))
            },
            via_device=(
                DOMAIN, coordinator.data.host_info.host_guid
            ),
        )


class GSAlarmGenerateIDsDeviceMixin(GSAlarmGenerateIDsMixinBase):
    """
    Mixin to generate IDs for device entities.

    Exposes `G90Device` object as `device` placeholder for the format strings.
    """
    @classmethod
    def generate_unique_id(
        cls, coordinator: GsAlarmCoordinator, obj: G90Device
    ) -> str:
        """
        Generate unique ID for the device.

        :param coordinator: The coordinator to use.
        :param obj: The device object to use.
        :return: The generated unique ID.
        """
        return super().generate_unique_id_with_placeholders(
            coordinator, {
                'device': obj,
                # Additional placeholder for device subindex (1-based), mostly
                # for user visible elements (e.g. entity ID)
                'device_subindex': obj.subindex + 1
            }
        )

    @classmethod
    def generate_entity_id(
        cls, coordinator: GsAlarmCoordinator,
        obj: G90Device
    ) -> str:
        """
        Generate entity ID for the device.

        :param coordinator: The coordinator to use.
        :param obj: The device object to use.
        :return: The generated entity ID.
        """
        return super().generate_entity_id_with_placeholders(
            coordinator, {'device': obj}
        )

    @classmethod
    def generate_device_info(
        cls, coordinator: GsAlarmCoordinator, obj: G90Device
    ) -> DeviceInfo:
        """
        Generate DeviceInfo for the device, will be linked via the parent
        HASS device.

        :param coordinator: The coordinator to use.
        :param obj: The device object to use.
        :return: The generated DeviceInfo.
        """
        if not coordinator.data.host_info:
            raise ValueError("Coordinator host info is not set")

        return DeviceInfo(
            manufacturer=MANUFACTURER,
            model=obj.type_name or '',
            name=obj.protocol_data.parent_name,
            serial_number=coordinator.data.host_info.host_guid,
            identifiers={
                (DOMAIN, cls.generate_unique_id_with_placeholders(
                    coordinator, {
                        # Subindex is always 0 to have single device for
                        # multi-node relays
                        'device': obj, 'device_subindex': 0
                    }
                ))
            },
            via_device=(
                DOMAIN, coordinator.data.host_info.host_guid
            ),
        )
