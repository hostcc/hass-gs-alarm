# SPDX-License-Identifier: MIT
# Copyright (c) 2022 Ilia Sotnikov
"""
Tests callbacks for the custom component.
"""
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)
from homeassistant.core import HomeAssistant
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelState,
)

from pyg90alarm import G90ArmDisarmTypes

from custom_components.gs_alarm.const import DOMAIN
from .conftest import (
    AlarmMockT, hass_get_state_by_unique_id, allow_callbacks_to_complete,
)

MAIN_SENSOR_UNIQUE_ID = 'dummy_guid_sensor_0'
TAMPERED_SENSOR_UNIQUE_ID = 'dummy_guid_sensor_0_tampered'
LOW_BATTERY_SENSOR_UNIQUE_ID = 'dummy_guid_sensor_0_low_battery'
OPEN_WHEN_ARMED_SENSOR_UNIQUE_ID = 'dummy_guid_sensor_0_open_when_armed'


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
    await allow_callbacks_to_complete(hass)

    # Simulate the alarm callback is triggered
    await mock_g90alarm.return_value.on_alarm(
        0, 'Dummy sensor', is_tampered=False
    )
    await allow_callbacks_to_complete(hass)

    # Verify panel state and attributes reflect that
    panel_state = hass_get_state_by_unique_id(
        hass, 'alarm_control_panel', 'dummy_guid'
    )

    assert panel_state.state == AlarmControlPanelState.TRIGGERED
    assert panel_state.attributes is not None
    assert panel_state.attributes.get('changed_by') == (
        'binary_sensor.dummy_guid_dummy_sensor'
    )

    # Simulate the arm callback is triggered
    await mock_g90alarm.return_value.on_armdisarm(
        G90ArmDisarmTypes.ARM_AWAY
    )
    await allow_callbacks_to_complete(hass)

    # Verify `changed_by` attribute has been reset
    panel_state = hass_get_state_by_unique_id(
        hass, 'alarm_control_panel', 'dummy_guid'
    )

    assert panel_state.attributes is not None
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
    await allow_callbacks_to_complete(hass)

    # Simulate the arm callback is triggered
    await mock_g90alarm.return_value.on_armdisarm(
        G90ArmDisarmTypes.ARM_AWAY
    )
    await allow_callbacks_to_complete(hass)

    # Verify panel state reflects that
    panel_state = hass_get_state_by_unique_id(
        hass, 'alarm_control_panel', 'dummy_guid'
    )

    assert panel_state.state == AlarmControlPanelState.ARMED_AWAY


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
    await allow_callbacks_to_complete(hass)

    # Simulate the disarm callback is triggered
    await mock_g90alarm.return_value.on_armdisarm(
        G90ArmDisarmTypes.DISARM
    )
    await allow_callbacks_to_complete(hass)

    # Verify panel state reflects that
    panel_state = hass_get_state_by_unique_id(
        hass, 'alarm_control_panel', 'dummy_guid'
    )

    assert panel_state.state == AlarmControlPanelState.DISARMED


async def test_low_battery_callback(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests the binary sensor and diagnostic entity go on when low battery is
    reported, then off when sensor activity clears the flag.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-low-battery-callbacks"
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    await mock_g90alarm.return_value.on_low_battery(
        0, 'Dummy sensor'
    )
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    )
    assert sensor_state.attributes != {}
    assert sensor_state.attributes.get('low_battery') is True
    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', LOW_BATTERY_SENSOR_UNIQUE_ID
    ).state == 'on'

    await mock_g90alarm.return_value.on_sensor_activity(
        0, 'Dummy sensor', False
    )
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    )
    assert sensor_state.attributes.get('low_battery') is False
    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', LOW_BATTERY_SENSOR_UNIQUE_ID
    ).state == 'off'


async def test_tamper_callback(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests the binary sensor and diagnostic entity go on when tamper is
    reported, then off when the panel is armed or disarmed.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-tamper-callbacks"
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    await mock_g90alarm.return_value.on_alarm(
        0, 'Dummy sensor', is_tampered=True
    )
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    )
    assert sensor_state.attributes != {}
    assert sensor_state.attributes.get('tampered') is True
    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', TAMPERED_SENSOR_UNIQUE_ID
    ).state == 'on'

    await mock_g90alarm.return_value.on_armdisarm(
        G90ArmDisarmTypes.DISARM
    )
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    )
    assert sensor_state.attributes.get('tampered') is False
    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', TAMPERED_SENSOR_UNIQUE_ID
    ).state == 'off'


async def test_door_open_when_arming_callback(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests the binary sensor and diagnostic entity go on when door open when
    arming is reported, then off when the panel is armed or disarmed.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-door-open-when-arming-callbacks"
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    await mock_g90alarm.return_value.on_door_open_when_arming(
        0, 'Dummy sensor'
    )
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    )
    assert sensor_state.attributes != {}
    assert sensor_state.attributes.get('door_open_when_arming') is True
    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', OPEN_WHEN_ARMED_SENSOR_UNIQUE_ID
    ).state == 'on'

    await mock_g90alarm.return_value.on_armdisarm(
        G90ArmDisarmTypes.DISARM
    )
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    )
    assert sensor_state.attributes.get('door_open_when_arming') is False
    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', OPEN_WHEN_ARMED_SENSOR_UNIQUE_ID
    ).state == 'off'
