# SPDX-License-Identifier: MIT
# Copyright (c) 2021 Ilia Sotnikov
"""
Binary sensors for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import Mapping, Any, TYPE_CHECKING
import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyg90alarm import (
    G90Sensor, G90PeripheralTypes, G90HostInfoWifiStatus, G90HostInfoGsmStatus
)

from .coordinator import GsAlarmCoordinator
from .mixin import GSAlarmGenerateIDsSensorMixin
from .entity_base import GSAlarmEntityBase
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry

HASS_SENSOR_TYPES_MAPPING = {
    G90PeripheralTypes.DOOR: BinarySensorDeviceClass.DOOR,
    G90PeripheralTypes.GLASS: BinarySensorDeviceClass.WINDOW,
    G90PeripheralTypes.GAS: BinarySensorDeviceClass.GAS,
    G90PeripheralTypes.SMOKE: BinarySensorDeviceClass.SMOKE,
    G90PeripheralTypes.SOS: BinarySensorDeviceClass.PROBLEM,
    G90PeripheralTypes.VIB: BinarySensorDeviceClass.VIBRATION,
    G90PeripheralTypes.WATER: BinarySensorDeviceClass.MOISTURE,
    G90PeripheralTypes.INFRARED: BinarySensorDeviceClass.MOTION,
    G90PeripheralTypes.IN_BEAM: BinarySensorDeviceClass.MOTION,
    G90PeripheralTypes.REMOTE: BinarySensorDeviceClass.LOCK,
    G90PeripheralTypes.RFID: BinarySensorDeviceClass.LOCK,
    G90PeripheralTypes.DOORBELL: BinarySensorDeviceClass.OCCUPANCY,
    G90PeripheralTypes.BUTTONID: BinarySensorDeviceClass.LOCK,
    G90PeripheralTypes.WATCH: BinarySensorDeviceClass.OCCUPANCY,
    G90PeripheralTypes.FINGER_LOCK: BinarySensorDeviceClass.LOCK,
    G90PeripheralTypes.SUBHOST: BinarySensorDeviceClass.CONNECTIVITY,
    G90PeripheralTypes.REMOTE_2_4G: BinarySensorDeviceClass.LOCK,
    G90PeripheralTypes.CORD_SENSOR: BinarySensorDeviceClass.MOTION,
    G90PeripheralTypes.SOCKET: BinarySensorDeviceClass.PLUG,
    G90PeripheralTypes.SIREN: BinarySensorDeviceClass.SOUND,
    G90PeripheralTypes.CURTAIN: BinarySensorDeviceClass.WINDOW,
    G90PeripheralTypes.SLIDINGWIN: BinarySensorDeviceClass.WINDOW,
    G90PeripheralTypes.AIRCON: BinarySensorDeviceClass.COLD,
    G90PeripheralTypes.TV: BinarySensorDeviceClass.CONNECTIVITY,
    G90PeripheralTypes.SOCKET_2_4G: BinarySensorDeviceClass.PLUG,
    G90PeripheralTypes.SIREN_2_4G: BinarySensorDeviceClass.SOUND,
    G90PeripheralTypes.SWITCH_2_4G: BinarySensorDeviceClass.POWER,
    G90PeripheralTypes.TOUCH_SWITCH_2_4G: BinarySensorDeviceClass.POWER,
    G90PeripheralTypes.CURTAIN_2_4G: BinarySensorDeviceClass.WINDOW,
    G90PeripheralTypes.CORD_DEV: BinarySensorDeviceClass.MOTION,
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    def sensor_list_change_callback(sensor: G90Sensor, added: bool) -> None:
        if added:
            # Register HASS entities for the new sensor and its attributes
            # exposed separately
            entities = [
                # Sensor itself
                G90BinarySensor(sensor, entry.runtime_data),
                # Sensor attributes
                G90SensorAttributeTampered(sensor, entry.runtime_data),
                G90SensorAttributeLowBattery(sensor, entry.runtime_data),
                G90SensorAttributeDoorOpenWhenArming(
                    sensor, entry.runtime_data
                ),
            ]

            async_add_entities(entities)

    # Register callback for panel's sensors added/removed
    entry.runtime_data.client.sensor_list_change_callback.add(
        sensor_list_change_callback
    )

    # Add WiFi, GSM and GPRS/3G status sensors
    async_add_entities([
        G90WifiStatusSensor(entry.runtime_data),
        G90GsmStatusSensor(entry.runtime_data),
        G90Gprs3GActiveSensor(entry.runtime_data),
    ])


class G90BinarySensor(
    BinarySensorEntity, CoordinatorEntity[GsAlarmCoordinator],
    GSAlarmGenerateIDsSensorMixin
):
    """
    Binary sensor for alarm panel's sensor.

    :param g90_sensor: Instance of `G90Sensor` representing the sensor.
    :param coordinator: Instance of `GsAlarmCoordinator` to coordinate updates.
    """
    # pylint:disable=too-many-instance-attributes

    UNIQUE_ID_FMT = "{guid}_sensor_{sensor.index}"
    ENTITY_ID_FMT = "{guid}_{sensor.name}"

    def __init__(
        self, g90_sensor: G90Sensor, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._g90_sensor = g90_sensor
        # Generate unique ID and entity ID
        self._attr_unique_id = self.generate_unique_id(coordinator, g90_sensor)
        self.entity_id = self.generate_entity_id(coordinator, g90_sensor)
        # Each sensor has dedicated HASS device
        self._attr_device_info = self.generate_device_info(
            coordinator, g90_sensor
        )
        self._attr_has_entity_name = True
        # Derive name from sensor's name
        self._attr_name = None
        self._attr_translation_key = 'sensor'
        self._attr_translation_placeholders = {
            'sensor': g90_sensor.name,
        }

        # Extra attributes over sensor characteristics, useful for
        # troubleshooting to identify sensor type and its number as panel
        # reports it
        try:
            subtype = G90PeripheralTypes(g90_sensor.subtype).name
        except ValueError:
            subtype = None

        self._attr_extra_state_attributes = {
            'panel_sensor_number': g90_sensor.index,
            'protocol': g90_sensor.protocol.name,
            'flags': g90_sensor.user_flags.name,
            'wireless': g90_sensor.is_wireless,
            'type': g90_sensor.type.name or '',
            'subtype': subtype,
            'definition':
                g90_sensor.definition.name if g90_sensor.definition else None,
        }
        hass_sensor_type = HASS_SENSOR_TYPES_MAPPING.get(g90_sensor.type, None)
        if hass_sensor_type:
            self._attr_device_class = hass_sensor_type

        # Register callbacks to handle sensor state changes
        g90_sensor.state_callback.add(self.state_callback)
        g90_sensor.low_battery_callback.add(self.low_battery_callback)
        g90_sensor.tamper_callback.add(self.tamper_callback)
        g90_sensor.door_open_when_arming_callback.add(
            self.door_open_when_arming_callback
        )

    async def async_added_to_hass(self) -> None:
        """
        Invoked by HASS when entity is added.
        """
        await super().async_added_to_hass()
        # Store the entity ID as extra data to `G90Sensor` instance, it will be
        # provided in the arguments when `G90Alarm.alarm_callback` is invoked
        _LOGGER.debug(
            'Storing entity ID as extra data: sensor %s (idx %s), ID: %s',
            self._g90_sensor.name, self._g90_sensor.index, self.entity_id
        )
        self._g90_sensor.extra_data = self.entity_id

    def state_callback(self, value: bool) -> None:
        """
        Invoked by `pyg90alarm` when its sensor changes the state.

        :param value: New state value.
        """
        _LOGGER.debug('%s: Received state callback: %s', self.unique_id, value)
        # Signal HASS to update the sensor's state, which will trigger the
        # `is_on()` method
        self.schedule_update_ha_state()

    def low_battery_callback(self) -> None:
        """
        Invoked by `pyg90alarm` when its sensor reports low battery condition.
        """
        _LOGGER.debug(
            '%s: Received low battery callback', self.unique_id
        )
        # Signal HASS to update the sensor's attributes, which will trigger the
        # `extra_state_attributes()` method
        self.schedule_update_ha_state()

    def tamper_callback(self) -> None:
        """
        Invoked by `pyg90alarm` when its sensor reports tampered condition.
        """
        _LOGGER.debug(
            '%s: Received tamper callback', self.unique_id
        )
        # Signal HASS to update the sensor's attributes, which will trigger the
        # `extra_state_attributes()` method
        self.schedule_update_ha_state()

    def door_open_when_arming_callback(self) -> None:
        """
        Invoked by `pyg90alarm` when its sensor reports door open when arming.
        """
        _LOGGER.debug(
            '%s: Received door open when arming callback', self.unique_id
        )
        # Signal HASS to update the sensor's attributes, which will trigger the
        # `extra_state_attributes()` method
        self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """
        Provides extra state attributes.
        """
        extra_attrs = self._attr_extra_state_attributes

        # Low battery is only applicable to wireless sensors
        if self._g90_sensor.is_wireless:
            extra_attrs['low_battery'] = self._g90_sensor.is_low_battery

        extra_attrs['tampered'] = self._g90_sensor.is_tampered
        extra_attrs['door_open_when_arming'] = (
            self._g90_sensor.is_door_open_when_arming
        )

        _LOGGER.debug(
            '%s: Providing extra attributes %s', self.unique_id,
            repr(extra_attrs)
        )

        return extra_attrs

    @property
    def is_on(self) -> bool | None:
        """
        Indicates if sensor is active.
        """
        val = (
            # None translates to unknown state in HASS for disabled sensor
            None if not self._g90_sensor.enabled
            else self._g90_sensor.occupancy
        )

        _LOGGER.debug('%s: Providing state %s', self.unique_id, val)
        return val


class G90SensorAttributeBase(
    BinarySensorEntity, CoordinatorEntity[GsAlarmCoordinator],
    GSAlarmGenerateIDsSensorMixin
):
    """
    Binary sensor representing a specific sensor attribute.

    :param g90_sensor: Instance of `G90Sensor` representing the sensor.
    :param coordinator: Instance of `GsAlarmCoordinator` to coordinate updates.
    :param sensor_attr: Name of the attribute on `G90Sensor` to monitor.
    """
    # pylint: disable=too-many-instance-attributes,too-many-arguments
    # pylint: disable=too-many-positional-arguments
    def __init__(
        self, g90_sensor: G90Sensor, coordinator: GsAlarmCoordinator,
        sensor_attr: str,
    ) -> None:
        super().__init__(coordinator)
        self._g90_sensor = g90_sensor
        self._attr_has_entity_name = True
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_translation_placeholders = {
            'sensor': g90_sensor.name,
        }
        self._sensor_attr = sensor_attr

        # Generate unique ID and entity ID
        self._attr_unique_id = self.generate_unique_id(coordinator, g90_sensor)
        self.entity_id = self.generate_entity_id(coordinator, g90_sensor)
        # Bind the sensor under the HASS device representing the panel's sensor
        self._attr_device_info = G90BinarySensor.generate_device_info(
            coordinator, g90_sensor
        )

        # Register callbacks to handle sensor attribute changes
        g90_sensor.tamper_callback.add(self.attr_callback)
        g90_sensor.low_battery_callback.add(self.attr_callback)
        g90_sensor.door_open_when_arming_callback.add(self.attr_callback)

    def attr_callback(self) -> None:
        """
        Callback invoked when a sensor attribute (e.g., tamper, low battery,
        door open when arming) changes the state.

        Triggers an update of the entity's state in Home Assistant.
        """
        _LOGGER.debug(
            '%s: Received attr callback', self.unique_id
        )
        # Signal HASS to update the sensor's attributes, which will trigger the
        # `extra_state_attributes()` method
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool | None:
        """
        Indicates if sensor is active.
        """
        val = (
            # None translates to unknown state in HASS for disabled sensor
            None if not self._g90_sensor.enabled
            else getattr(self._g90_sensor, self._sensor_attr)
        )

        _LOGGER.debug('%s: Providing state %s', self.unique_id, val)
        return val


class G90SensorAttributeTampered(G90SensorAttributeBase):
    """
    Binary sensor for the tampered sensor attribute.

    :param g90_sensor: Instance of `G90Sensor` representing the sensor.
    :param coordinator: Instance of `GsAlarmCoordinator` to coordinate updates.
    """
    # pylint: disable=too-many-instance-attributes,too-many-arguments
    # pylint: disable=too-many-positional-arguments,too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_{sensor.index}_tampered"
    ENTITY_ID_FMT = "{guid}_{sensor.name}_tampered"

    def __init__(
        self, sensor: G90Sensor, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(sensor, coordinator, 'is_tampered')
        self._attr_translation_key = 'sensor_tampered'
        self._attr_icon = 'mdi:shield-alert'


class G90SensorAttributeLowBattery(G90SensorAttributeBase):
    """
    Binary sensor for the low battery sensor attribute.

    :param g90_sensor: Instance of `G90Sensor` representing the sensor.
    :param coordinator: Instance of `GsAlarmCoordinator` to coordinate updates.
    """
    # pylint: disable=too-many-instance-attributes,too-many-arguments
    # pylint: disable=too-many-positional-arguments,too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_{sensor.index}_low_battery"
    ENTITY_ID_FMT = "{guid}_{sensor.name}_low_battery"

    def __init__(
        self, sensor: G90Sensor, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(sensor, coordinator, 'is_low_battery')
        self._attr_translation_key = 'sensor_low_battery'
        self._attr_icon = 'mdi:battery-alert'


class G90SensorAttributeDoorOpenWhenArming(G90SensorAttributeBase):
    """
    Binary sensor for the door open when arming sensor attribute.
    """
    # pylint: disable=too-many-instance-attributes,too-many-arguments
    # pylint: disable=too-many-positional-arguments,too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_{sensor.index}_open_when_armed"
    ENTITY_ID_FMT = "{guid}_{sensor.name}_open_when_armed"

    def __init__(
        self, sensor: G90Sensor, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(sensor, coordinator, 'is_door_open_when_arming')
        self._attr_translation_key = 'sensor_active_when_arming'
        self._attr_icon = 'mdi:door-open'


class G90WifiStatusSensor(
    BinarySensorEntity, GSAlarmEntityBase,
):
    """
    WiFi status sensor.

    :param coordinator: Instance of `GsAlarmCoordinator` to coordinate updates.
    """
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_wifi_status"
    ENTITY_ID_FMT = "{guid}_wifi_status"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_translation_key = 'wifi_status'
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        host_info = self.coordinator.data.host_info
        self._attr_is_on = (
            host_info.wifi_status == G90HostInfoWifiStatus.OPERATIONAL
        )
        self.async_write_ha_state()


class G90GsmStatusSensor(
    BinarySensorEntity, GSAlarmEntityBase,
):
    """
    GSM status sensor.

    :param coordinator: Instance of `GsAlarmCoordinator` to coordinate updates.
    """
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_gsm_status"
    ENTITY_ID_FMT = "{guid}_gsm_status"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_translation_key = 'gsm_status'

        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        host_info = self.coordinator.data.host_info
        self._attr_is_on = (
            host_info.gsm_status == G90HostInfoGsmStatus.OPERATIONAL
        )
        self.async_write_ha_state()


class G90Gprs3GActiveSensor(
    GSAlarmEntityBase, BinarySensorEntity
):
    """
    GPRS/3G status sensor.

    :param coordinator: Instance of `GsAlarmCoordinator` to coordinate updates.
    """
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_gprs_3g_active"
    ENTITY_ID_FMT = "{guid}_gprs_3g_active"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_translation_key = 'gprs_3g_active'
        self._attr_icon = 'mdi:signal-3g'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        host_info = self.coordinator.data.host_info
        self._attr_is_on = host_info.gprs_3g_active
        self.async_write_ha_state()
