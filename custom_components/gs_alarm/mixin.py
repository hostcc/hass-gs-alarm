# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Mixin classes for `gs-alarm` integration.
"""
from __future__ import annotations
from typing import Optional, Any, Dict, Generic, TypeVar
from abc import ABC, abstractmethod
import logging

from homeassistant.util import slugify
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.config_entries import ConfigEntry

from pyg90alarm import G90Sensor, G90Device

from .const import DOMAIN, MANUFACTURER, CONF_RESTORE_STATE_AT_STARTUP
from .coordinator import GsAlarmCoordinator


_LOGGER = logging.getLogger(__name__)
T = TypeVar('T')


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
    ENTITY_DOMAIN: Optional[str] = None

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

        if not cls.ENTITY_DOMAIN:
            raise NotImplementedError("ENTITY_DOMAIN is not defined")

        # Entity ID must use the Home Assistant entity platform domain
        # (e.g. switch, binary_sensor) as the first segment, not the
        # integration domain.
        return f'{cls.ENTITY_DOMAIN}.{slugify(
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


class GsAlarmRestoreStateMixinBase(RestoreEntity, Generic[T], ABC):
    """
    Base mixin for state restoration.
    """
    @classmethod
    @abstractmethod
    def _parse_state(cls, state_str: str) -> T | None:
        """
        Parse a recorded Home Assistant state string into a value of concrete
        type. Subclasses must implement this method.

        :param state_str: The state string from the recorder.
        :return: Parsed value, or None if strict and state is not on/off.
        """

    @staticmethod
    def _restore_state_at_startup_enabled(
        config_entry: Optional[ConfigEntry]  # pylint: disable=unused-argument
    ) -> bool:
        """
        Whether state restoration at startup is enabled for this entry.
        """
        return True

    async def restore_state(
        self, config_entry: Optional[ConfigEntry]
    ) -> T | None:
        """
        Read and parse the last recorded state from Home Assistant.

        :return: Parsed value of concrete type, or None if restore should not
         apply.
        """
        if not self._restore_state_at_startup_enabled(config_entry):
            _LOGGER.debug(
                'Restore state at startup is disabled for %s',
                self.unique_id
            )
            return None

        state = await self.async_get_last_state()
        # No state could be restored
        if state is None:
            return None

        # Parse the state string into a value of concrete type
        restored = self._parse_state(state.state)

        if restored is not None:
            _LOGGER.debug(
                'Restored state for %s: %s',
                self.unique_id, state.state
            )

        return restored


class GsAlarmSensorRestoreGatedMixinBase(GsAlarmRestoreStateMixinBase[T]):
    """
    Base mixin for state restoration gated by the ``restore_state_at_startup``
    config entry option.

    Restored state is used until the panel reports a live update.
    """
    def _init_restore_state(self) -> None:
        """
        Initialize per-instance restore state attributes.
        """
        # Use the presence of the attribute to detect if the restore state
        # has been initialized already - prevents multiple initialization
        # clearing out the restored state.
        if hasattr(self, '_use_restored_state'):
            return

        self._use_restored_state: bool = False
        self._restored_state: T | None = None

    @staticmethod
    def _restore_state_at_startup_enabled(
        config_entry: Optional[ConfigEntry]
    ) -> bool:
        """
        Whether state restoration at startup is enabled for this entry.
        """
        if config_entry is None:
            return False

        # Use the option value to determine if state restoration is enabled
        return bool(
            config_entry.options.get(CONF_RESTORE_STATE_AT_STARTUP, True)
        )

    async def restore_state(
        self, config_entry: Optional[ConfigEntry]
    ) -> None:
        """
        Restore the last recorded state if the option is enabled.
        """
        self._init_restore_state()
        restored = await super().restore_state(config_entry)
        if restored is None:
            return

        # Store the restored state and mark it as used
        self._restored_state = restored
        self._use_restored_state = True

    def state_with_restore(self, live_state: T | None) -> T | None:
        """
        Return restored state if active, otherwise the live panel value.
        """
        self._init_restore_state()
        if self._use_restored_state:
            return self._restored_state

        return live_state

    def clear_restored_state(self) -> None:
        """
        Clear restored state override so live panel values are used.
        """
        self._init_restore_state()
        self._use_restored_state = False


class GsAlarmRestoreBoolMixin(GsAlarmRestoreStateMixinBase[bool]):
    """
    Mixin for binary sensor entities with boolean state restoration.
    """
    @classmethod
    def _parse_state(cls, state_str: str) -> bool | None:
        """
        Parse a recorded Home Assistant state string into a boolean value.
        """
        return {STATE_ON: True, STATE_OFF: False}.get(state_str, None)


class GsAlarmRestoreBoolGatedMixin(
    GsAlarmSensorRestoreGatedMixinBase[bool], GsAlarmRestoreBoolMixin
):
    """
    Mixin for binary sensor entities with boolean state restoration gated by
    the config entry option (see above).
    """
