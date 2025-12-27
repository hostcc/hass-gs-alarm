# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Select entities for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import Event

from pyg90alarm import (
    G90Sensor, G90Error, G90TimeoutError, G90SensorAlertModes,
    G90SensorDefinitions, G90DeviceDefinitions,
)

from .const import DOMAIN
from .mixin import GSAlarmGenerateIDsSensorMixin
from .entity_base import GSAlarmEntityBase
from .coordinator import GsAlarmCoordinator
from .binary_sensor import G90BinarySensor
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    def sensor_list_change_callback(sensor: G90Sensor, added: bool) -> None:
        # Add select entity for alert mode if a new sensor is added
        if added:
            async_add_entities(
                [G90SensorAlertMode(sensor, entry.runtime_data)]
            )

    # Register the callback for sensor list changes
    entry.runtime_data.client.sensor_list_change_callback.add(
        sensor_list_change_callback
    )

    # Entities for registering sensors holding its name and type
    async_add_entities([
        G90NewSensorType(entry.runtime_data),
        G90NewDeviceType(entry.runtime_data),
    ])


class G90SensorAlertMode(
    SelectEntity, CoordinatorEntity[GsAlarmCoordinator],
    GSAlarmGenerateIDsSensorMixin
):
    """
    Select entity for alert mode of the sensor.

    :param sensor: The sensor to create the entity for.
    :param coordinator: The coordinator to use.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    states_map = {
        G90SensorAlertModes.ALERT_ALWAYS:
            "alert_always",
        G90SensorAlertModes.ALERT_WHEN_AWAY:
            "alert_when_away",
        G90SensorAlertModes.ALERT_WHEN_AWAY_AND_HOME:
            "alert_when_away_and_home",
    }
    reverse_states_map = dict(
        zip(states_map.values(), states_map.keys())
    )

    UNIQUE_ID_FMT = "{guid}_sensor_{sensor.index}_alert_mode"
    ENTITY_ID_FMT = "{guid}_{sensor.name}_alert_mode"

    def __init__(
        self, sensor: G90Sensor, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._sensor = sensor
        # Generate unique ID and entity ID
        self._attr_unique_id = self.generate_unique_id(coordinator, sensor)
        self.entity_id = self.generate_entity_id(coordinator, sensor)
        # The select entity is bound to the HASS device representing the sensor
        self._attr_device_info = G90BinarySensor.generate_device_info(
            coordinator, sensor
        )

        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = 'mdi:shield-alert'
        self._attr_has_entity_name = True
        self._attr_translation_key = 'sensor_alert_mode'
        self._attr_translation_placeholders = {
            'sensor': sensor.name,
        }
        self._attr_options = list(self.states_map.values())

    @property
    def current_option(self) -> str | None:
        """
        Return the currently selected option.

        :return: The option.
        """
        return self.states_map.get(self._sensor.alert_mode, None)

    async def async_select_option(self, option: str) -> None:
        """
        Set the mode of the sensor.

        :param option: The option to set.
        """
        try:
            # Select component should ensure the correct option is
            # selected
            await self._sensor.set_alert_mode(self.reverse_states_map[option])
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error setting alert mode for sensor '%s': %s",
                self.unique_id,
                repr(exc)
            )


class G90NewEntitySelectBase(
    SelectEntity, GSAlarmEntityBase,
):
    """
    Base class for select entity of new sensor or relay type.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors
    def __init__(
        self, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)

        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = 'mdi:list-box'
        self._attr_has_entity_name = True
        self._attr_current_option = None

    async def async_select_option(self, option: str) -> None:
        """
        Store the selected option.

        :param option: The option.
        """
        self._attr_current_option = option
        self.async_write_ha_state()

    async def handle_registration_event(self, event: Event) -> None:
        """
        Handle custom HASS event to reset the selection.

        :param event: The HASS event.
        """
        # Ensure the event is for this panel
        if event.data['guid'] != self.coordinator.data.host_info.host_guid:
            return

        # Reset the current option
        self._attr_current_option = None
        self.async_write_ha_state()


class G90NewSensorType(G90NewEntitySelectBase):
    """
    Select entity for new sensor type.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_new_sensor_type"
    ENTITY_ID_FMT = "{guid}_new_sensor_type"

    def __init__(
        self, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'new_sensor_type'
        self._attr_options = [
            x.name for x in G90SensorDefinitions.definitions()
        ]
        # The select entity listens for registration events to reset its value
        self.coordinator.hass.bus.async_listen(
            f"{DOMAIN}_new_sensor_registration", self.handle_registration_event
        )


class G90NewDeviceType(G90NewEntitySelectBase):
    """
    Select entity for new relay type.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_new_device_type"
    ENTITY_ID_FMT = "{guid}_new_device_type"

    def __init__(
        self, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._attr_translation_key = 'new_device_type'
        self._attr_options = [
            x.name for x in G90DeviceDefinitions.definitions()
        ]
        # The select entity listens for registration events to reset its value
        self.coordinator.hass.bus.async_listen(
            f"{DOMAIN}_new_device_registration", self.handle_registration_event
        )
