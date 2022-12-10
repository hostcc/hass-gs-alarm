"""
Tests callbacks for the custom component.
"""
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)
from pyg90alarm.const import G90ArmDisarmTypes

from custom_components.gs_alarm import (
    async_setup_entry,
)
from custom_components.gs_alarm.const import DOMAIN


@pytest.mark.g90host_status(
    result=G90ArmDisarmTypes.DISARM
)
async def test_alarm_callback(hass, mock_g90alarm):
    """
    Tests the alarm panel changes its state upon alarm callback is triggered.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-alarm-callbacks"
    )

    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    # Simulate the alarm callback is triggered
    mock_g90alarm.return_value.alarm_callback(
        1, 'Dummy', 'binary_sensor.dummy_1'
    )

    # Verify panel state and attributes reflect that
    panel_state = hass.states.get('alarm_control_panel.dummy')
    assert panel_state.state == 'triggered'
    assert panel_state.attributes.get('changed_by') == 'binary_sensor.dummy_1'


@pytest.mark.g90host_status(
    result=G90ArmDisarmTypes.DISARM
)
async def test_arm_callback(hass, mock_g90alarm):
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

    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    # Simulate the arm callback is triggered
    mock_g90alarm.return_value.armdisarm_callback(
        G90ArmDisarmTypes.ARM_AWAY
    )

    # Verify panel state reflects that
    panel_state = hass.states.get('alarm_control_panel.dummy')
    assert panel_state.state == 'armed_away'


@pytest.mark.g90host_status(
    result=G90ArmDisarmTypes.ARM_AWAY
)
async def test_disarm_callback(hass, mock_g90alarm):
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

    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    # Simulate the disarm callback is triggered
    mock_g90alarm.return_value.armdisarm_callback(
        G90ArmDisarmTypes.DISARM
    )

    # Verify panel state reflects that
    panel_state = hass.states.get('alarm_control_panel.dummy')
    assert panel_state.state == 'disarmed'
