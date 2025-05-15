"""
Select entities for `gs_alarm` integration.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.util import slugify
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    EntityCategory,
)
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyg90alarm import (
    G90Sensor, G90Error, G90TimeoutError, G90SensorAlertModes,
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
    g90sensors_mode: List[SelectEntity] = []
    for sensor in (
        hass.data[DOMAIN][entry.entry_id].panel_sensors
    ):
        g90sensors_mode.append(
            G90SensorAlertMode(sensor, hass.data[DOMAIN][entry.entry_id])
        )

    async_add_entities(g90sensors_mode)


class G90SensorAlertMode(SelectEntity):
    """
    Select entity for alert mode of the sensor.
    """
    # Not all base class methods are meaningfull in the context of the
    # integration, silence the `pylint` for those
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

    def __init__(self, sensor: G90Sensor, hass_data: GsAlarmData) -> None:
        self._sensor = sensor
        self._attr_device_info = hass_data.device
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_unique_id = slugify(
            f"{hass_data.guid}_sensor_{sensor.index}_alert_mode"
        )
        self._attr_has_entity_name = True
        self._attr_translation_key = 'sensor_alert_mode'
        self._attr_translation_placeholders = {
            'sensor': sensor.name,
        }
        self._attr_options = list(self.states_map.values())

    @property
    def current_option(self) -> str | None:
        return self.states_map.get(self._sensor.alert_mode, None)

    async def async_select_option(self, option: str) -> None:
        """
        Set the mode of the sensor.
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
