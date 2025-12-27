# SPDX-License-Identifier: MIT
# Copyright (c) 2021 Ilia Sotnikov
"""
Alarm control panel component.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelEntityFeature, AlarmControlPanelState,
)

from pyg90alarm import G90ArmDisarmTypes, G90Error, G90TimeoutError

from .entity_base import GSAlarmEntityBase
from .coordinator import GsAlarmCoordinator
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry

_LOGGER = logging.getLogger(__name__)


# Mapping between `pyg90alarm` states for the panel and ones for HomeAssitant
STATE_MAPPING = {
    G90ArmDisarmTypes.ARM_AWAY: AlarmControlPanelState.ARMED_AWAY,
    G90ArmDisarmTypes.ARM_HOME: AlarmControlPanelState.ARMED_HOME,
    G90ArmDisarmTypes.DISARM: AlarmControlPanelState.DISARMED,
    G90ArmDisarmTypes.ALARMED: AlarmControlPanelState.TRIGGERED,
}


async def async_setup_entry(
    _hass: HomeAssistant, entry: GsAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    async_add_entities([G90AlarmPanel(entry.runtime_data)])


class G90AlarmPanel(
    AlarmControlPanelEntity, GSAlarmEntityBase,
):
    """
    Instantiate entity for alarm control panel.

    :param coordinator: The coordinator to use.
    """
    # pylint: disable=abstract-method, too-many-instance-attributes
    # pylint: disable=too-many-ancestors
    UNIQUE_ID_FMT = "{guid}"
    ENTITY_ID_FMT = "{guid}"

    def __init__(self, coordinator: GsAlarmCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_AWAY
        )
        self._attr_code_arm_required = False
        # Derive name from the device GUID, will be used to compose
        # entity ID comprising of the GUID alone
        self._attr_name = None
        self._attr_has_entity_name = True
        self._attr_changed_by = None
        self._attr_alarm_state = None
        self.coordinator.client.armdisarm_callback.add(self.armdisarm_callback)
        self.coordinator.client.alarm_callback.add(self.alarm_callback)

    def armdisarm_callback(self, state: G90ArmDisarmTypes) -> None:
        """
        Invoked by `G90Alarm` when panel is armed or disarmed.
        """
        _LOGGER.debug('Received arm/disarm callback: %s', state)
        self._attr_alarm_state = STATE_MAPPING[state]
        # Reset `changed_by` attribute so the value it possibly has (name of
        # sensor caused last alarm) isn't carried on indefinitely which might
        # be confusing
        self._attr_changed_by = None
        # Update HA entity since the panel state has changed
        self.async_write_ha_state()

    def alarm_callback(
        self, sensor_idx: int, sensor_name: str, extra_data: str
    ) -> None:
        """
        Invoked by `G90Alarm` whan alarm is triggered.

        :param sensor_idx: Index of the sensor (specific attribute of the
         sensor in the alarm panel, not index in the sensors list) triggered
         the alarm
        :param sensor_name: Name of the sensor (as known to alarm panel)
         triggered the alarm
        :param extra_data: Extra data might have been set to the
         `G90Sensor` instance via `G90Sensor.extra_data` associated with the
         alarm. The integration stores ID of sensor entity there, so it is
         extracted and used for `changed_by` attribute of the HASS alarm panel
        """
        _LOGGER.debug(
            'Received alarm callback: %s (idx=%s), entity id: %s',
            sensor_name, sensor_idx, extra_data
        )
        # Set `changed_by` panel attribute to the sensor entity ID if available
        # in `extra_data`
        if extra_data:
            self._attr_changed_by = extra_data
        self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
        # Update HA entity since the panel state has changed
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Invoked by the coordinator when data is updated.
        """
        _LOGGER.debug('Updating state')

        host_state = self.coordinator.data.host_status.host_status
        self._attr_alarm_state = STATE_MAPPING[host_state]
        _LOGGER.debug(
            '%s: Providing state %s', self.unique_id, self._attr_alarm_state
        )
        self.async_write_ha_state()

    async def async_alarm_disarm(self, _code: str | None = None) -> None:
        """Send disarm command."""
        try:
            await self.coordinator.client.disarm()
        except (G90Error, G90TimeoutError) as exc:
            # Log the error, the state is not altered since next update
            # should read back the previous state unchanged
            _LOGGER.error(
                "Error disarming panel '%s': %s",
                self.unique_id,
                repr(exc)
            )

    async def async_alarm_arm_home(self, _code: str | None = None) -> None:
        """Send arm home command."""
        try:
            await self.coordinator.client.arm_home()
        except (G90Error, G90TimeoutError) as exc:
            # See comment above
            _LOGGER.error(
                "Error arming panel '%s' home: %s",
                self.unique_id,
                repr(exc)
            )

    async def async_alarm_arm_away(self, _code: str | None = None) -> None:
        """Send arm away command."""
        try:
            await self.coordinator.client.arm_away()
        except (G90Error, G90TimeoutError) as exc:
            # See comment above
            _LOGGER.error(
                "Error arming panel '%s' away: %s",
                self.unique_id,
                repr(exc)
            )
