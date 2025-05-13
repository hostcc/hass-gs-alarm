"""
Switch entities for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING, List
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    EntityCategory,
)
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyg90alarm import (
    G90Device, G90Sensor, G90Error, G90TimeoutError,
    G90SensorUserFlags, G90AlertConfigFlags,
)

from .const import DOMAIN
if TYPE_CHECKING:
    from . import GsAlarmData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    g90switches: List[SwitchEntity] = []
    for device in (
        hass.data[DOMAIN][entry.entry_id].panel_devices
    ):
        g90switches.append(
            G90Switch(device, hass.data[DOMAIN][entry.entry_id])
        )

    for sensor in (
        hass.data[DOMAIN][entry.entry_id].panel_sensors
    ):
        if sensor.supports_updates:
            g90switches.extend([
                G90SensorFlag(
                    sensor, hass.data[DOMAIN][entry.entry_id],
                    G90SensorUserFlags.ENABLED, "Enabled"
                ),
                G90SensorFlag(
                    sensor, hass.data[DOMAIN][entry.entry_id],
                    G90SensorUserFlags.ARM_DELAY, "Arm delay"
                ),
                G90SensorFlag(
                    sensor, hass.data[DOMAIN][entry.entry_id],
                    G90SensorUserFlags.DETECT_DOOR, "Detect door"
                ),
                G90SensorFlag(
                    sensor, hass.data[DOMAIN][entry.entry_id],
                    G90SensorUserFlags.DOOR_CHIME, "Door chime"
                ),
                G90SensorFlag(
                    sensor, hass.data[DOMAIN][entry.entry_id],
                    G90SensorUserFlags.INDEPENDENT_ZONE, "Independent zone"
                ),
            ])

    g90switches.extend([
        G90AlertConfigFlag(
            hass.data[DOMAIN][entry.entry_id],
            G90AlertConfigFlags.AC_POWER_FAILURE, "AC Power failure"
        ),
        G90AlertConfigFlag(
            hass.data[DOMAIN][entry.entry_id],
            G90AlertConfigFlags.AC_POWER_RECOVER, "AC Power recover"
        ),
        G90AlertConfigFlag(
            hass.data[DOMAIN][entry.entry_id],
            G90AlertConfigFlags.ARM_DISARM, "Arm disarm"
        ),
        G90AlertConfigFlag(
            hass.data[DOMAIN][entry.entry_id],
            G90AlertConfigFlags.HOST_LOW_VOLTAGE, "Host low voltage"
        ),
        G90AlertConfigFlag(
            hass.data[DOMAIN][entry.entry_id],
            G90AlertConfigFlags.SENSOR_LOW_VOLTAGE, "Sensor low voltage"
        ),
        G90AlertConfigFlag(
            hass.data[DOMAIN][entry.entry_id],
            G90AlertConfigFlags.WIFI_AVAILABLE, "WiFi available"
        ),
        G90AlertConfigFlag(
            hass.data[DOMAIN][entry.entry_id],
            G90AlertConfigFlags.WIFI_UNAVAILABLE, "WiFi unavailable"
        ),
        G90AlertConfigFlag(
            hass.data[DOMAIN][entry.entry_id],
            G90AlertConfigFlags.DOOR_OPEN, "Door open"
        ),
        G90AlertConfigFlag(
            hass.data[DOMAIN][entry.entry_id],
            G90AlertConfigFlags.DOOR_CLOSE, "Door close"
        ),
        G90AlertConfigFlag(
            hass.data[DOMAIN][entry.entry_id],
            G90AlertConfigFlags.SMS_PUSH, "SMS push"
        ),
    ])

    async_add_entities(g90switches)


class G90Switch(SwitchEntity):
    # Not all base class methods are meaningfull in the context of the
    # integration, silence the `pylint` for those
    # pylint: disable=abstract-method
    """
    Switch specific to the alarm panel's device (relay).
    """
    def __init__(self, device: G90Device, hass_data: GsAlarmData) -> None:
        self._device = device
        self._state = False
        self._attr_unique_id = (
            f"{hass_data.guid}_switch_{device.index}_{device.subindex + 1}"
        )
        self._attr_name = device.name
        self._attr_device_info = hass_data.device
        self._hass_data = hass_data

    @property
    def is_on(self) -> bool:
        """
        Indicates if the switch is active (on).
        """
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
            self._state = True

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
            self._state = False


class G90SensorFlag(SwitchEntity):
    # Not all base class methods are meaningfull in the context of the
    # integration, silence the `pylint` for those
    # pylint: disable=abstract-method
    """
    Switch entity for configuration option of the sensor.
    """
    def __init__(
        self, sensor: G90Sensor, hass_data: GsAlarmData,
        flag: G90SensorUserFlags, flag_name: str
    ) -> None:
        self._sensor = sensor
        self._flag = flag
        self._attr_unique_id = (
            f"{hass_data.guid}_sensor_{sensor.index}_{flag_name.lower()}"
        )
        self._attr_name = f"{sensor.name}: {flag_name}"
        self._attr_device_info = hass_data.device
        self._hass_data = hass_data
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        """
        Indicates if the switch is active (on).
        """
        value = self._sensor.get_flag(self._flag)
        _LOGGER.debug(
            "%s: Sensor flag '%s' is %s",
            self.unique_id, self._flag.name, value
        )
        return value

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


class G90AlertConfigFlag(SwitchEntity):
    # Not all base class methods are meaningfull in the context of the
    # integration, silence the `pylint` for those
    # pylint: disable=abstract-method
    """
    Switch entity for alert configuration option of the panel.
    """
    def __init__(
        self, hass_data: GsAlarmData, flag: G90AlertConfigFlags, flag_name: str
    ) -> None:
        self._flag = flag
        self._attr_unique_id = f"{hass_data.guid}_{flag_name.lower()}"
        self._attr_name = f"Alert: {flag_name}"
        self._attr_device_info = hass_data.device
        self._hass_data = hass_data
        self._attr_entity_category = EntityCategory.CONFIG

    async def async_added_to_hass(self) -> None:
        # Signal HASS to update the state as soon as component is added,
        # which will trigger the `async_update` method - that will provide
        # the up-to-date state w/o waiting for next interval
        await self.async_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        """
        Indicates if the switch is active (on).
        """
        value = await self._hass_data.client.alert_config.get_flag(self._flag)
        _LOGGER.debug(
            "%s: Alert config flag '%s' is %s",
            self.unique_id, self._flag.name, value
        )
        self._attr_is_on = value

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """
        Turn on the switch.
        """
        try:
            _LOGGER.debug(
                "%s: Switching on the alert config flag '%s'",
                self.unique_id, self._flag.name
            )
            await self._hass_data.client.alert_config.set_flag(
                self._flag, True
            )
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error switching on the alert config flag '%s': %s",
                self.unique_id,
                repr(exc)
            )

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """
        Turn off the switch.
        """
        try:
            _LOGGER.debug(
                "%s: Switching off the alert config flag '%s'",
                self.unique_id, self._flag.name
            )
            await self._hass_data.client.alert_config.set_flag(
                self._flag, False
            )
        except (G90Error, G90TimeoutError) as exc:
            _LOGGER.error(
                "Error switching off the alert config flag '%s': %s",
                self.unique_id,
                repr(exc)
            )
