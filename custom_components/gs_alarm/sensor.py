# SPDX-License-Identifier: MIT
# Copyright (c) 2021 Ilia Sotnikov
"""
Sensors for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, callback
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import (
    EntityCategory, PERCENTAGE, UnitOfElectricPotential,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity_base import GSAlarmEntityBase
from .coordinator import GsAlarmCoordinator
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry


async def async_setup_entry(_hass: HomeAssistant, entry: GsAlarmConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up a config entry."""

    # Sensors for WiFi and GSM signal, last device and last upstream packets
    g90sensors = [
        G90WifiSignal(entry.runtime_data),
        G90GsmSignal(entry.runtime_data),
        G90LastDevicePacket(entry.runtime_data),
        G90LastUpstreamPacket(entry.runtime_data),
        G90CellularOperator(entry.runtime_data),
        G90BatteryVoltage(entry.runtime_data),
    ]
    async_add_entities(g90sensors)


class G90BaseSensor(
    SensorEntity, GSAlarmEntityBase,
):
    """
    Base class for sensors.

    :param coordinator: The coordinator to use.
    """
    # pylint:disable=too-few-public-methods
    # pylint: disable=too-many-ancestors
    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_native_value = None
        self._attr_has_entity_name = True


class G90WifiSignal(G90BaseSensor):
    """
    Sensor for WiFi signal strength.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_wifi_signal"
    ENTITY_ID_FMT = "{guid}_wifi_signal"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'wifi_signal'
        self._attr_icon = 'mdi:wifi'
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        host_info = self.coordinator.data.host_info
        self._attr_native_value = host_info.wifi_signal_level
        self.async_write_ha_state()


class G90GsmSignal(G90BaseSensor):
    """
    Sensor for GSM signal strength.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_gsm_signal"
    ENTITY_ID_FMT = "{guid}_gsm_signal"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'gsm_signal'
        self._attr_icon = 'mdi:signal'
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        host_info = self.coordinator.data.host_info
        self._attr_native_value = host_info.gsm_signal_level
        self.async_write_ha_state()


class G90LastDevicePacket(G90BaseSensor):
    """
    Sensor for last device packet.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_last_device_packet"
    ENTITY_ID_FMT = "{guid}_last_device_packet"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'last_device_packet'
        self._attr_icon = 'mdi:clock-check'
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        self._attr_native_value = self.coordinator.data.last_device_packet_time
        self.async_write_ha_state()


class G90LastUpstreamPacket(G90BaseSensor):
    """
    Sensor for last upstream packet.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_last_upstream_packet"
    ENTITY_ID_FMT = "{guid}_last_upstream_packet"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'last_upstream_packet'
        self._attr_icon = 'mdi:cloud-clock'
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        self._attr_native_value = (
            self.coordinator.data.last_upstream_packet_time
        )
        self.async_write_ha_state()


class G90CellularOperator(G90BaseSensor):
    """
    Sensor for cellular operator code.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_cellular_operator"
    ENTITY_ID_FMT = "{guid}_cellular_operator"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'cellular_operator'
        self._attr_icon = 'mdi:cellphone-information'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        self._attr_native_value = (
            self.coordinator.data.net_config.gsm_operator
        )
        self.async_write_ha_state()


class G90BatteryVoltage(G90BaseSensor):
    """
    Sensor for panel battery voltage.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_battery_voltage"
    ENTITY_ID_FMT = "{guid}_battery_voltage"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'battery_voltage'
        self._attr_icon = 'mdi:battery'
        self._attr_native_unit_of_measurement = (
            UnitOfElectricPotential.MILLIVOLT
        )
        self._attr_suggested_display_precision = 2
        self._attr_suggested_unit_of_measurement = (
            UnitOfElectricPotential.VOLT
        )
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the sensor state.
        """
        voltage_str = self.coordinator.data.host_info.battery_voltage
        # The value is string, convert to int (millivolts), otherwise set to
        # None if conversion fails
        try:
            voltage_mv = int(voltage_str)
            self._attr_native_value = voltage_mv
        except ValueError:
            self._attr_native_value = None
        self.async_write_ha_state()
