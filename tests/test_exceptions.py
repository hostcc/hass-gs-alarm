"""
Tests for exception handling by the custom component.
"""
from datetime import timedelta
from unittest.mock import AsyncMock
import pytest

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
   SERVICE_ALARM_ARM_AWAY,
   SERVICE_ALARM_ARM_HOME,
   SERVICE_ALARM_DISARM,
   SERVICE_TURN_ON,
   SERVICE_TURN_OFF,
   STATE_OFF,
)
from homeassistant.components.alarm_control_panel.const import (
    DOMAIN as ALARM_DOMAIN, AlarmControlPanelState,
)
from homeassistant.components.switch.const import (
    DOMAIN as SWITCH_DOMAIN
)

from pyg90alarm import G90TimeoutError, G90Error
from custom_components.gs_alarm.const import DOMAIN
from .conftest import (
    AlarmMockT, hass_get_entity_id_by_unique_id, hass_get_state_by_unique_id
)


@pytest.mark.parametrize(
    "failed_g90_method,simulated_error,expected_entry_state", [
        ('get_host_info', G90TimeoutError, ConfigEntryState.SETUP_RETRY),
        ('get_host_info', G90Error, ConfigEntryState.SETUP_ERROR),
        ('get_devices', G90TimeoutError, ConfigEntryState.SETUP_RETRY),
        ('get_devices', G90Error, ConfigEntryState.SETUP_ERROR),
        ('get_sensors', G90TimeoutError, ConfigEntryState.SETUP_RETRY),
        ('get_sensors', G90Error, ConfigEntryState.SETUP_ERROR),
        # The simulated errors below will trigger inside entry update listener,
        # and won't result in state being error
        (
            'start_simulating_alerts_from_history',
            G90Error, ConfigEntryState.LOADED
        ),
        (
            'stop_simulating_alerts_from_history',
            G90Error, ConfigEntryState.LOADED
        ),
    ]
)
async def test_setup_entry_exception(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT, failed_g90_method: str,
    simulated_error: Exception, expected_entry_state: ConfigEntryState
) -> None:
    """
    Tests the custom integration properly handles exceptions during the setup.
    """
    # Simulate the error in specific `G90Alarm` method
    getattr(
       mock_g90alarm.return_value, failed_g90_method
    ).side_effect = simulated_error

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={
            # Required for `G90Alarm.stop_simulating_alerts_from_history()`
            # method to be called
            'simulate_alerts_from_history': False
        },
        entry_id="test-exc"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify the entity is in expected state
    assert config_entry.state == expected_entry_state


async def test_alarm_panel_state_update_exception(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests the custom integration properly handles exceptions when updating the
    state.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-exc"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    # Simulate the error in `G90Alarm.get_host_info()` method that is used to
    # fetch panel's state. The simulated error is set after entry is loaded, so
    # that execution comes to state update
    mock_g90alarm.return_value.get_host_info.side_effect = G90Error

    # Simulate some time has passed for HomeAssistant to invoke
    # `async_update()` for components
    async_fire_time_changed(hass, dt.utcnow() + timedelta(hours=1))
    await hass.async_block_till_done()

    # Verify the panel's state is unknown
    panel_state = hass_get_state_by_unique_id(
        hass, 'alarm_control_panel', 'dummy_guid'
    )

    assert panel_state.state == AlarmControlPanelState.DISARMED


@pytest.mark.parametrize("failed_service,failed_g90_method", [
    (SERVICE_ALARM_DISARM, 'disarm'),
    (SERVICE_ALARM_ARM_HOME, 'arm_home'),
    (SERVICE_ALARM_ARM_AWAY, 'arm_away'),
])
@pytest.mark.parametrize("simulated_error", [
    G90Error,
    G90TimeoutError,
])
async def test_alarm_panel_service_exception(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT,
    failed_service: str, failed_g90_method: str, simulated_error: Exception
) -> None:
    """
    Tests the custom integration properly handles exceptions during service
    calls to alarm panel.
    """
    # Simulate the error in specific `G90Alarm` method
    getattr(
        mock_g90alarm.return_value, failed_g90_method
    ).side_effect = simulated_error

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-exc"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'alarm_control_panel', 'dummy_guid'
    )

    entity = hass.states.get(entity_id)
    assert entity is not None, (
        f'State for entity {entity_id} not found'
    )

    # Perform the call
    await hass.services.async_call(
        ALARM_DOMAIN, failed_service,
        {'entity_id': entity.entity_id},
        blocking=True
    )

    # Verify the panel's state is left unchanged - `mock_g90alarm` simulates
    # the panel is disarmed during initial setup
    assert entity.state == AlarmControlPanelState.DISARMED


@pytest.mark.parametrize("failed_service,failed_g90_method", [
    (SERVICE_TURN_ON, 'turn_on'),
    (SERVICE_TURN_OFF, 'turn_off'),
    (SERVICE_TURN_ON, None),
    (SERVICE_TURN_OFF, None),
])
@pytest.mark.parametrize("simulated_error", [
    G90Error,
    G90TimeoutError,
])
async def test_switch_service_exception(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT,
    failed_service: str, failed_g90_method: str, simulated_error: Exception
) -> None:
    """
    Tests the custom integration properly handles exceptions during service
    calls to switches of the alarm panel.
    """
    if failed_g90_method:
        # Simulate the error in specific `G90Alarm` method
        setattr(
            (await mock_g90alarm.return_value.get_devices())[0],
            failed_g90_method,
            AsyncMock(side_effect=simulated_error)
        )

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-exc"
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'switch', 'dummy_guid_switch_0_1'
    )
    entity = hass.states.get(entity_id)
    assert entity is not None, (
        f'State for entity {entity_id} not found'
    )

    await hass.services.async_call(
        SWITCH_DOMAIN, failed_service,
        {'entity_id': entity.entity_id},
        blocking=True
    )

    # Verify the switch's state is left unchanged - `G90Switch` initializes it
    # to off
    assert entity.state == STATE_OFF
