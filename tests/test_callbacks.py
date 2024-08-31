"""
Tests callbacks for the custom component.
"""
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)
from homeassistant.core import HomeAssistant
from homeassistant.const import (
   STATE_ALARM_DISARMED,
   STATE_ALARM_ARMED_AWAY,
   STATE_ALARM_TRIGGERED,
)

from pyg90alarm import G90ArmDisarmTypes

from custom_components.gs_alarm.const import DOMAIN
from .conftest import AlarmMockT


@pytest.mark.g90host_status(
    result=G90ArmDisarmTypes.DISARM
)
async def test_alarm_callback(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests the alarm panel changes its state upon alarm callback is triggered.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-alarm-callbacks"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Simulate the alarm callback is triggered
    mock_g90alarm.return_value.alarm_callback(
        1, 'Dummy', 'binary_sensor.dummy_1'
    )

    # Verify panel state and attributes reflect that
    panel_state = hass.states.get('alarm_control_panel.dummy_guid')
    assert panel_state is not None
    assert panel_state.state == STATE_ALARM_TRIGGERED
    assert panel_state.attributes.get('changed_by') == 'binary_sensor.dummy_1'

    # Simulate the arm callback is triggered
    mock_g90alarm.return_value.armdisarm_callback(
        G90ArmDisarmTypes.ARM_AWAY
    )
    # Verify `changed_by` attribute has been reset
    panel_state = hass.states.get('alarm_control_panel.dummy_guid')
    assert panel_state is not None
    assert panel_state.attributes.get('changed_by') is None


@pytest.mark.g90host_status(
    result=G90ArmDisarmTypes.DISARM
)
async def test_arm_callback(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests the alarm panel changes its state upon arm callback is triggered for
    arming away.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-arm-callbacks"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Simulate the arm callback is triggered
    mock_g90alarm.return_value.armdisarm_callback(
        G90ArmDisarmTypes.ARM_AWAY
    )

    # Verify panel state reflects that
    panel_state = hass.states.get('alarm_control_panel.dummy_guid')
    assert panel_state is not None
    assert panel_state.state == STATE_ALARM_ARMED_AWAY


@pytest.mark.g90host_status(
    result=G90ArmDisarmTypes.ARM_AWAY
)
async def test_disarm_callback(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests the alarm panel changes its state upon arm callback is triggered for
    disarming.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-disarm-callbacks"
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Simulate the disarm callback is triggered
    mock_g90alarm.return_value.armdisarm_callback(
        G90ArmDisarmTypes.DISARM
    )

    # Verify panel state reflects that
    panel_state = hass.states.get('alarm_control_panel.dummy_guid')
    assert panel_state is not None
    assert panel_state.state == STATE_ALARM_DISARMED
