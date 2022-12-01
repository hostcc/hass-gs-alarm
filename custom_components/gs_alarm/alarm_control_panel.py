"""
tbd
"""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)

from pyg90alarm.const import G90ArmDisarmTypes

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# Mapping between `pyg90alarm` states for the panel and ones for HomeAssitant
STATE_MAPPING = {
    G90ArmDisarmTypes.ARM_AWAY: STATE_ALARM_ARMED_AWAY,
    G90ArmDisarmTypes.ARM_HOME: STATE_ALARM_ARMED_HOME,
    G90ArmDisarmTypes.DISARM: STATE_ALARM_DISARMED,
    G90ArmDisarmTypes.ALARMED: STATE_ALARM_TRIGGERED,
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up a config entry."""
    async_add_entities([G90AlarmPanel(hass.data[DOMAIN][entry.entry_id])])


class G90AlarmPanel(AlarmControlPanelEntity):
    """
    tbd
    """
    def __init__(self, hass_data: dict) -> None:
        self._attr_unique_id = hass_data['guid']
        self._attr_supported_features = (
            SUPPORT_ALARM_ARM_AWAY | SUPPORT_ALARM_ARM_HOME
        )
        self._attr_name = hass_data['guid']
        self._attr_device_info = hass_data['device']
        self._attr_changed_by = None
        self._state = None
        self._hass_data = hass_data
        self._hass_data['client'].armdisarm_callback = self.armdisarm_callback
        self._hass_data['client'].alarm_callback = self.alarm_callback

    async def add_to_platform_finish(self) -> None:
        """
        Invoked by HASS when platform is added.
        """
        # Read the state of the alarm panel upon entry is added to the
        # platform, but before its state is persisted. This helps HomeAssistant
        # to reflect the panel state right upon startup, not delaying to next
        # poll cycle
        await self.async_update()
        await super().add_to_platform_finish()

    def armdisarm_callback(self, state):
        """
        Invoked by `G90Alarm` when panel is armed or disarmed.
        """
        _LOGGER.debug('Received arm/disarm callback: %s', state)
        self._state = STATE_MAPPING[state]
        # Schedule updating HA since the panel state has changed
        self.schedule_update_ha_state()

    def alarm_callback(self, _sensor_idx, sensor_name):
        """
        Invoked by `G90Alarm` whan alarm is triggered.
        """
        _LOGGER.debug('Received alarm callback: %s', sensor_name)
        self._attr_changed_by = sensor_name
        # Schedule updating HA since the panel state has changed
        self.schedule_update_ha_state()

    async def async_update(self):
        """
        Invoked by HASS when state needs an update.
        """
        _LOGGER.debug('Updating state')

        host_status = await self._hass_data['client'].get_host_status()
        host_state = host_status.host_status
        self._state = STATE_MAPPING[host_state]
        # Store alarm panel information (GSM/WiFi status/signal level etc.) so
        # a sensor could use the data w/o duplicate access to `host_info`
        # property of `G90Alarm`, which issues a device call internally
        self._hass_data['host_info'] = (
            await self._hass_data['client'].get_host_info()
        )

    @property
    def state(self):
        """
        Returns the platform state.
        """
        return self._state

    async def async_alarm_disarm(self, _code: str | None = None) -> None:
        """Send disarm command."""
        await self._hass_data['client'].disarm()

    async def async_alarm_arm_home(self, _code: str | None = None) -> None:
        """Send arm home command."""
        await self._hass_data['client'].arm_home()

    async def async_alarm_arm_away(self, _code: str | None = None) -> None:
        """Send arm away command."""
        await self._hass_data['client'].arm_away()
