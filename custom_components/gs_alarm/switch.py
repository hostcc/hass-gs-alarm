# SPDX-License-Identifier: MIT
# Copyright (c) 2021 Ilia Sotnikov
"""
Switch entities for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING
import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.const import EntityCategory
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pyg90alarm import (
    G90Device, G90Sensor, G90Error, G90TimeoutError,
    G90SensorUserFlags, G90AlertConfigFlags,
)

from .entity_base import GsAlarmSwitchRestoreEntityBase
from .mixin import (
    GSAlarmGenerateIDsDeviceMixin, GSAlarmGenerateIDsSensorMixin,
    GSAlarmGenerateIDsCommonMixin
)
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
    def device_list_change_callback(device: G90Device, added: bool) -> None:
        # Add switch entity for the relay if it was added
        if added:
            async_add_entities(
                [G90Switch(device, entry.runtime_data)]
            )

    def sensor_list_change_callback(sensor: G90Sensor, added: bool) -> None:
        # Add sensor configuration switches if sensor was added and it
        # supports updates
        if added and sensor.supports_updates:
            switches = [
                G90SensorFlag(
                    sensor, entry.runtime_data,
                    G90SensorUserFlags.ENABLED,
                    'mdi:check-circle',
                ),
                G90SensorFlag(
                    sensor, entry.runtime_data,
                    G90SensorUserFlags.ARM_DELAY,
                    'mdi:timer-sand',
                ),
                G90SensorFlag(
                    sensor, entry.runtime_data,
                    G90SensorUserFlags.DETECT_DOOR,
                    'mdi:door',
                ),
                G90SensorFlag(
                    sensor, entry.runtime_data,
                    G90SensorUserFlags.DOOR_CHIME,
                    'mdi:bell',
                ),
                G90SensorFlag(
                    sensor, entry.runtime_data,
                    G90SensorUserFlags.INDEPENDENT_ZONE,
                    'mdi:lock',
                ),
            ]
            async_add_entities(switches)

    # Register callbacks for sensor/device list changes
    entry.runtime_data.client.device_list_change_callback.add(
        device_list_change_callback
    )

    entry.runtime_data.client.sensor_list_change_callback.add(
        sensor_list_change_callback
    )

    # Alert configuration switches for the panel
    config_switches = [
        G90AlertConfigFlag(
            entry.runtime_data,
            G90AlertConfigFlags.AC_POWER_FAILURE,
            'mdi:power-plug-off',
        ),
        G90AlertConfigFlag(
            entry.runtime_data,
            G90AlertConfigFlags.AC_POWER_RECOVER,
            'mdi:power-plug',
        ),
        G90AlertConfigFlag(
            entry.runtime_data,
            G90AlertConfigFlags.ARM_DISARM,
            'mdi:shield-home',
        ),
        G90AlertConfigFlag(
            entry.runtime_data,
            G90AlertConfigFlags.HOST_LOW_VOLTAGE,
            'mdi:battery-alert',
        ),
        G90AlertConfigFlag(
            entry.runtime_data,
            G90AlertConfigFlags.SENSOR_LOW_VOLTAGE,
            'mdi:battery-alert',
        ),
        G90AlertConfigFlag(
            entry.runtime_data,
            G90AlertConfigFlags.WIFI_AVAILABLE,
            'mdi:wifi',
        ),
        G90AlertConfigFlag(
            entry.runtime_data,
            G90AlertConfigFlags.WIFI_UNAVAILABLE,
            'mdi:wifi-off',
        ),
        G90AlertConfigFlag(
            entry.runtime_data,
            G90AlertConfigFlags.DOOR_OPEN,
            'mdi:door-open',
        ),
        G90AlertConfigFlag(
            entry.runtime_data,
            G90AlertConfigFlags.DOOR_CLOSE,
            'mdi:door-closed',
        ),
        G90AlertConfigFlag(
            entry.runtime_data,
            G90AlertConfigFlags.SMS_PUSH,
            'mdi:message-text',
        ),
        G90SmsAlertWhenArmed(entry.runtime_data),
        G90SimulateAlertsFromHistory(entry.runtime_data),
    ]

    async_add_entities(config_switches)


class G90Switch(
    SwitchEntity, CoordinatorEntity[GsAlarmCoordinator],
    GSAlarmGenerateIDsDeviceMixin
):
    """
    Switch for the alarm panel's relay.

    :param device: G90Device instance representing the relay.
    :param coordinator: The coordinator to use.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_switch_{device.index}_{device_subindex}"
    ENTITY_ID_FMT = "{guid}_{device.name}"

    def __init__(
        self, device: G90Device, coordinator: GsAlarmCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._state = False
        self._attr_has_entity_name = True
        self._attr_name = None

        if device.node_count > 1:
            # Resulting name will be combination of HASS device name and the
            # index in multi-node switch, based on how HASS names the entities
            # having `has_entity_name` set to `True`
            self._attr_name = device.name

        # Generate unique ID and entity ID
        self._attr_unique_id = self.generate_unique_id(coordinator, device)
        self.entity_id = self.generate_entity_id(coordinator, device)
        # Each relay has dedicated HASS device (single one for multi-node
        # relays)
        self._attr_device_info = self.generate_device_info(coordinator, device)

        self._attr_translation_key = 'relay'
        self._attr_translation_placeholders = {
            'relay': device.name,
        }

    async def async_added_to_hass(self) -> None:
        """
        Invoked by HASS when entity is added.
        """
        await super().async_added_to_hass()
        # Store the entity ID as extra data to `G90Sensor` instance, it will be
        # provided in the arguments when `G90Alarm.alarm_callback` is invoked
        _LOGGER.debug(
            'Storing entity ID as extra data: device %s (idx %s), ID: %s',
            self._device.name, self._device.index, self.entity_id
        )
        self._device.extra_data = self.entity_id

    @property
    def is_on(self) -> bool:
        """
        Indicates if the switch is active (on).
        """
        _LOGGER.debug(
            "Providing state for switch '%s': %s", self.unique_id, self._state
        )
        return self._state

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """
        Turn on the switch.
        """
        try:
            await self._device.turn_on()
        except (G90Error, G90TimeoutError) as exc:
            # State isn't set to STATE_UNKNOWN since the panel doesn't support
            # reading it back
            _LOGGER.error(
                "Error turning on the switch '%s': %s",
                self.unique_id,
                repr(exc)
            )
        else:
            # State is only updated upon successful command execution
            _LOGGER.debug("Switch '%s' turned on", self.unique_id)
            self._state = True
            self.async_write_ha_state()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """
        Turn off the switch.
        """
        try:
            await self._device.turn_off()
        except (G90Error, G90TimeoutError) as exc:
            # See comment above
            _LOGGER.error(
                "Error turning off the switch '%s': %s",
                self.unique_id,
                repr(exc)
            )
        else:
            # See comment above
            _LOGGER.debug("Switch '%s' turned off", self.unique_id)
            self._state = False
            self.async_write_ha_state()


class G90SensorFlag(
    SwitchEntity, CoordinatorEntity[GsAlarmCoordinator],
    GSAlarmGenerateIDsSensorMixin
):
    """
    Switch entity for configuration option of the sensor.

    :param sensor: G90Sensor instance representing the sensor.
    :param coordinator: The coordinator to use.
    :param flag: The sensor user flag this switch controls.
    :param icon: The icon to use for the switch entity.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_sensor_{sensor.index}_{flag_name}"
    ENTITY_ID_FMT = "{guid}_{sensor.name}_{flag_name}"

    def __init__(
        self, sensor: G90Sensor, coordinator: GsAlarmCoordinator,
        flag: G90SensorUserFlags, icon: str
    ) -> None:
        super().__init__(coordinator)
        self._sensor = sensor
        self._flag = flag
        # Bind the switch under the HASS device representing the panel's sensor
        self._attr_device_info = G90BinarySensor.generate_device_info(
            coordinator, sensor
        )
        # Generate unique ID and entity ID using sensor and flag name
        self._attr_unique_id = self.generate_unique_id_with_placeholders(
            coordinator, {
                'sensor': sensor,
                'flag_name': flag.name,
            }
        )
        self.entity_id = self.generate_entity_id_with_placeholders(
            coordinator, {
                'sensor': sensor,
                'flag_name': flag.name,
            }
        )

        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = icon
        self._attr_has_entity_name = True
        self._attr_translation_key = f'sensor_flag_{str(flag.name).lower()}'

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the switch state.
        """
        # `sensor` of entity data is periodically updated by coordinator thru
        # `get_sensors()`
        self._attr_is_on = self._sensor.get_flag(self._flag)
        _LOGGER.debug(
            "%s: Sensor flag '%s' is %s",
            self.unique_id, self._flag.name, self._attr_is_on
        )
        self.async_write_ha_state()

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """
        Turn on the switch.
        """
        try:
            _LOGGER.debug(
                "%s: Switching on the sensor flag '%s'",
                self.unique_id, self._flag.name
            )
            await self._sensor.set_flag(self._flag, True)
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error switching on the sensor flag '%s': %s",
                self.unique_id,
                repr(exc)
            )

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """
        Turn off the switch.
        """
        try:
            _LOGGER.debug(
                "%s: Switching off the sensor flag '%s'",
                self.unique_id, self._flag.name
            )
            await self._sensor.set_flag(self._flag, False)
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error switching off the sensor flag '%s': %s",
                self.unique_id,
                repr(exc)
            )

        await self.coordinator.async_request_refresh()


class G90AlertConfigFlag(
    SwitchEntity, CoordinatorEntity[GsAlarmCoordinator],
    GSAlarmGenerateIDsCommonMixin
):
    """
    Switch entity for alert configuration option of the panel.

    :param coordinator: The coordinator to use.
    :param flag: The alert config flag this switch controls.
    :param icon: The icon to use for the switch entity.
    """
    # pylint: disable=abstract-method,too-many-instance-attributes
    # pylint: disable=too-many-ancestors

    UNIQUE_ID_FMT = "{guid}_alert_config_flag_{flag_name}"
    ENTITY_ID_FMT = "{guid}_alert_config_flag_{flag_name}"

    def __init__(
        self, coordinator: GsAlarmCoordinator,
        flag: G90AlertConfigFlags, icon: str
    ) -> None:
        super().__init__(coordinator)
        self._flag = flag
        self._attr_has_entity_name = True
        # The switch is bound to the HASS device for the alarm panel itself
        self._attr_device_info = self.generate_parent_device_info(coordinator)
        # Generate unique ID and entity ID using flag name
        self._attr_unique_id = self.generate_unique_id_with_placeholders(
            coordinator, {
                'flag_name': flag.name,
            }
        )
        self.entity_id = self.generate_entity_id_with_placeholders(
            coordinator, {
                'flag_name': flag.name,
            }
        )

        self._attr_translation_key = (
            f'alert_config_flag_{str(flag.name).lower()}'
        )
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = icon

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked when HomeAssistant needs to update the switch state.
        """
        alert_config_flags = self.coordinator.data.alert_config_flags
        self._attr_is_on = self._flag in alert_config_flags
        _LOGGER.debug(
            "%s: Alert config flag '%s' is %s",
            self.unique_id, self._flag.name, self._attr_is_on
        )
        self.async_write_ha_state()

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """
        Turn on the switch.
        """
        try:
            _LOGGER.debug(
                "%s: Switching on the alert config flag '%s'",
                self.unique_id, self._flag.name
            )
            await self.coordinator.client.alert_config.set_flag(
                self._flag, True
            )
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error switching on the alert config flag '%s': %s",
                self.unique_id,
                repr(exc)
            )

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """
        Turn off the switch.
        """
        try:
            _LOGGER.debug(
                "%s: Switching off the alert config flag '%s'",
                self.unique_id, self._flag.name
            )
            await self.coordinator.client.alert_config.set_flag(
                self._flag, False
            )
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error switching off the alert config flag '%s': %s",
                self.unique_id,
                repr(exc)
            )

        await self.coordinator.async_request_refresh()


class G90SimulateAlertsFromHistory(GsAlarmSwitchRestoreEntityBase):
    """
    Switch entity to configure simulating alerts from history.
    """
    # pylint: disable=too-many-ancestors
    UNIQUE_ID_FMT = "{guid}_simulate_alerts_from_history"
    ENTITY_ID_FMT = "{guid}_simulate_alerts_from_history"

    def __init__(
        self, coordinator: GsAlarmCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_translation_key = 'simulate_alerts_from_history'
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = 'mdi:history'

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """
        Turn on the switch.
        """
        try:
            _LOGGER.debug('Starting to simulate device alerts from history')
            await (
                self.coordinator.client.start_simulating_alerts_from_history()
            )
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error enabling simulation of alerts from history"
                " for panel '%s': %s",
                self.coordinator.data.host_info.host_guid,
                repr(exc)
            )
        else:
            # Store the state only if enabling simulation succeeded
            await super().async_turn_on()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """
        Turn off the switch.
        """
        try:
            _LOGGER.debug('Stopping to simulate device alerts from history')
            await self.coordinator.client.stop_simulating_alerts_from_history()
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error disabling simulation of alerts from history"
                " for panel '%s': %s",
                self.coordinator.data.host_info.host_guid,
                repr(exc)
            )
        else:
            # Store the state only if disabling simulation succeeded
            await super().async_turn_off()


class G90SmsAlertWhenArmed(GsAlarmSwitchRestoreEntityBase):
    """
    Switch entity to configure SMS alerts only when panel is armed.
    """
    # pylint: disable=too-many-ancestors
    UNIQUE_ID_FMT = "{guid}_sms_alert_when_armed"
    ENTITY_ID_FMT = "{guid}_sms_alert_when_armed"

    def __init__(
        self, coordinator: GsAlarmCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_translation_key = 'sms_alert_when_armed'
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = 'mdi:message-text'

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """
        Turn on the switch.
        """
        _LOGGER.debug(
            'Enabling SMS alert when armed for panel %s',
            self.coordinator.data.host_info.host_guid
        )
        # No exception handling since this property doesn't
        # communicate with the panel directly
        self.coordinator.client.sms_alert_when_armed = True
        # Store the state
        await super().async_turn_on()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """
        Turn off the switch.
        """
        _LOGGER.debug(
            'Disabling SMS alert when armed for panel %s',
            self.coordinator.data.host_info.host_guid
        )
        # See comment above
        self.coordinator.client.sms_alert_when_armed = False
        await super().async_turn_off()
