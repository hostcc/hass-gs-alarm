# SPDX-License-Identifier: MIT
# Copyright (c) 2021 Ilia Sotnikov
"""
Tests for switches from the custom component.
"""
from __future__ import annotations
from typing import Optional
from datetime import timedelta
from unittest.mock import call
from operator import attrgetter
import pytest

from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    MockConfigEntry,
    mock_restore_cache,
)

from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
    STATE_ON, STATE_OFF,
)
from homeassistant.components.switch.const import (
    DOMAIN as SWITCH_DOMAIN
)

from pyg90alarm import G90SensorUserFlags, G90AlertConfigFlags, G90Error

from custom_components.gs_alarm.const import DOMAIN
from .conftest import AlarmMockT, hass_get_entity_id_by_unique_id


@pytest.mark.parametrize(
    "unique_id,service_call,expected_flag,expected_value",
    [
        pytest.param(
            "dummy_guid_sensor_0_enabled", SERVICE_TURN_ON,
            G90SensorUserFlags.ENABLED, True,
            id="Enable sensor"
        ),
        pytest.param(
            "dummy_guid_sensor_0_enabled", SERVICE_TURN_OFF,
            G90SensorUserFlags.ENABLED, False,
            id="Disable sensor"
        ),
        pytest.param(
            "dummy_guid_sensor_0_arm_delay", SERVICE_TURN_ON,
            G90SensorUserFlags.ARM_DELAY, True,
            id="Enable arm delay"
        ),
        pytest.param(
            "dummy_guid_sensor_0_arm_delay", SERVICE_TURN_OFF,
            G90SensorUserFlags.ARM_DELAY, False,
            id="Disable arm delay"
        ),
        pytest.param(
            "dummy_guid_sensor_0_detect_door", SERVICE_TURN_ON,
            G90SensorUserFlags.DETECT_DOOR, True,
            id="Enable detect door"
        ),
        pytest.param(
            "dummy_guid_sensor_0_detect_door", SERVICE_TURN_OFF,
            G90SensorUserFlags.DETECT_DOOR, False,
            id="Disable detect door"
        ),
        pytest.param(
            "dummy_guid_sensor_0_door_chime", SERVICE_TURN_ON,
            G90SensorUserFlags.DOOR_CHIME, True,
            id="Enable door chime"
        ),
        pytest.param(
            "dummy_guid_sensor_0_door_chime", SERVICE_TURN_OFF,
            G90SensorUserFlags.DOOR_CHIME, False,
            id="Disable door chime"
        ),
        pytest.param(
            "dummy_guid_sensor_0_independent_zone", SERVICE_TURN_ON,
            G90SensorUserFlags.INDEPENDENT_ZONE, True,
            id="Enable independent zone"
        ),
        pytest.param(
            "dummy_guid_sensor_0_independent_zone", SERVICE_TURN_OFF,
            G90SensorUserFlags.INDEPENDENT_ZONE, False,
            id="Disable independent zone"
        ),
    ],
)
# pylint: disable=too-many-positional-arguments,too-many-arguments
async def test_sensor_flags(
    unique_id: str, service_call: str,
    expected_flag: G90SensorUserFlags, expected_value: bool,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests sensor flags are set correctly thru corresponding switches.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_sensor_flags"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'switch', unique_id
    )

    # Change the sensor flag thru state of corresponding switch
    await hass.services.async_call(
        SWITCH_DOMAIN,
        service_call,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Verify the sensor flag was set correctly
    sensor = (await mock_g90alarm.return_value.get_sensors())[0]
    sensor.set_flag.assert_called_once_with(expected_flag, expected_value)


async def test_sensor_flags_exception(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests exceptions are properly handled changing sensor user flags.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_sensor_flags_exception"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    # Simulate some time has passed for HomeAssistant to invoke
    # update for components
    async_fire_time_changed(hass, dt.utcnow() + timedelta(hours=1))
    await hass.async_block_till_done()

    # Simulate an exception when setting the sensor flag
    sensor = (await mock_g90alarm.return_value.get_sensors())[0]
    sensor.set_flag.side_effect = G90Error('dummy exception')

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'switch', 'dummy_guid_sensor_0_enabled'
    )

    # Attempt to turn off the switch for the sensor enabled flag
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Verify the switch for the sensor enabled flag is still on
    dummy_sensor_1_enabled = hass.states.get(entity_id)
    assert dummy_sensor_1_enabled is not None
    assert dummy_sensor_1_enabled.state == 'on'

    # Attempt to turn on the switch - no exception should be raised
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )


@pytest.mark.parametrize(
    "unique_id,service_call,expected_call,expected_args",
    [
        pytest.param(
            "dummy_guid_alert_config_flag_ac_power_failure", SERVICE_TURN_ON,
            'alert_config.set_flag',
            (G90AlertConfigFlags.AC_POWER_FAILURE, True),
            id="AC power failure enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_ac_power_failure", SERVICE_TURN_OFF,
            'alert_config.set_flag',
            (G90AlertConfigFlags.AC_POWER_FAILURE, False),
            id="AC power failure disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_wifi_available", SERVICE_TURN_ON,
            'alert_config.set_flag',
            (G90AlertConfigFlags.WIFI_AVAILABLE, True),
            id="WiFi available enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_wifi_available", SERVICE_TURN_OFF,
            'alert_config.set_flag',
            (G90AlertConfigFlags.WIFI_AVAILABLE, False),
            id="WiFi available disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_wifi_unavailable", SERVICE_TURN_ON,
            'alert_config.set_flag',
            (G90AlertConfigFlags.WIFI_UNAVAILABLE, True),
            id="WiFi unavailable enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_wifi_unavailable", SERVICE_TURN_OFF,
            'alert_config.set_flag',
            (G90AlertConfigFlags.WIFI_UNAVAILABLE, False),
            id="WiFi unavailable disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_door_open", SERVICE_TURN_ON,
            'alert_config.set_flag',
            (G90AlertConfigFlags.DOOR_OPEN, True),
            id="Door open enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_door_open", SERVICE_TURN_OFF,
            'alert_config.set_flag',
            (G90AlertConfigFlags.DOOR_OPEN, False),
            id="Door open disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_door_close", SERVICE_TURN_ON,
            'alert_config.set_flag',
            (G90AlertConfigFlags.DOOR_CLOSE, True),
            id="Door close enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_door_close", SERVICE_TURN_OFF,
            'alert_config.set_flag',
            (G90AlertConfigFlags.DOOR_CLOSE, False),
            id="Door close disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_sms_push", SERVICE_TURN_ON,
            'alert_config.set_flag',
            (G90AlertConfigFlags.SMS_PUSH, True),
            id="SMS push enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_sms_push", SERVICE_TURN_OFF,
            'alert_config.set_flag',
            (G90AlertConfigFlags.SMS_PUSH, False),
            id="SMS push disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_arm_disarm", SERVICE_TURN_ON,
            'alert_config.set_flag',
            (G90AlertConfigFlags.ARM_DISARM, True),
            id="Arm disarm enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_arm_disarm", SERVICE_TURN_OFF,
            'alert_config.set_flag',
            (G90AlertConfigFlags.ARM_DISARM, False),
            id="Arm disarm disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_host_low_voltage", SERVICE_TURN_ON,
            'alert_config.set_flag',
            (G90AlertConfigFlags.HOST_LOW_VOLTAGE, True),
            id="Host low voltage enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_host_low_voltage", SERVICE_TURN_OFF,
            'alert_config.set_flag',
            (G90AlertConfigFlags.HOST_LOW_VOLTAGE, False),
            id="Host low voltage disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_sensor_low_voltage", SERVICE_TURN_ON,
            'alert_config.set_flag',
            (G90AlertConfigFlags.SENSOR_LOW_VOLTAGE, True),
            id="Sensor low voltage enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_sensor_low_voltage",
            SERVICE_TURN_OFF,
            'alert_config.set_flag',
            (G90AlertConfigFlags.SENSOR_LOW_VOLTAGE, False),
            id="Sensor low voltage disabled"
        ),
        pytest.param(
            "dummy_guid_sms_alert_when_armed", SERVICE_TURN_ON,
            None, ('sms_alert_when_armed', True),
            id="SMS alert when armed enabled"
        ),
        pytest.param(
            "dummy_guid_sms_alert_when_armed", SERVICE_TURN_OFF,
            None, ('sms_alert_when_armed', False),
            id="SMS alert when armed disabled"
        ),
        pytest.param(
            "dummy_guid_simulate_alerts_from_history", SERVICE_TURN_ON,
            'start_simulating_alerts_from_history', (),
            id="Simulate alerts from history enabled"
        ),
        pytest.param(
            "dummy_guid_simulate_alerts_from_history", SERVICE_TURN_OFF,
            'stop_simulating_alerts_from_history', (),
            id="Simulate alerts from history disabled"
        ),
    ],
)
# pylint: disable=too-many-positional-arguments,too-many-arguments
async def test_config_flags(
    unique_id: str, service_call: str,
    expected_call: Optional[str],
    expected_args: tuple[G90AlertConfigFlags | str, bool],
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:

    """
    Tests alert config flags are set correctly thru corresponding switches.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_config_flags"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'switch', unique_id
    )

    # Change the alert config flag thru state of corresponding switch
    await hass.services.async_call(
        SWITCH_DOMAIN,
        service_call,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Verify the alert config flag was set correctly
    if expected_call is None:
        # `expected_args` are interpreted as property name and value to
        # verify
        (prop, value) = expected_args
        assert getattr(mock_g90alarm.return_value, str(prop)) == value
    else:
        # Verify the expected method was called with expected arguments
        mock_g90alarm.return_value.assert_has_calls([
            getattr(call, expected_call)(*expected_args),
        ])


@pytest.mark.parametrize(
    "unique_id,service_call,simulated_exception,expected_call,expected_state",
    [
        # It is sufficient to test only single config flag switch for exception
        # handling, other switches share same code paths
        pytest.param(
            "dummy_guid_alert_config_flag_host_low_voltage", SERVICE_TURN_ON,
            G90Error('dummy exception'),
            'alert_config.set_flag',
            # The state comes from mocked initial value of the flag being ON,
            # hence the simulated exception doesn't affect it, only exception
            # handling is tested
            'on',
            id="Exception when enabling host low voltage alert"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_host_low_voltage", SERVICE_TURN_OFF,
            G90Error('dummy exception'),
            'alert_config.set_flag',
            # See comment above
            'on',
            id="Exception when disabling host low voltage alert"
        ),
        pytest.param(
            "dummy_guid_simulate_alerts_from_history", SERVICE_TURN_ON,
            G90Error('dummy exception'),
            'start_simulating_alerts_from_history', 'off',
            id="Exception when starting simulate alerts from history"
        ),
        pytest.param(
            "dummy_guid_simulate_alerts_from_history", SERVICE_TURN_OFF,
            G90Error('dummy exception'),
            'stop_simulating_alerts_from_history', 'on',
            id="Exception when stopping simulate alerts from history"
        ),
    ]
)
async def test_config_flags_exception(
    unique_id: str, service_call: str, simulated_exception: Exception,
    expected_call: str, expected_state: str,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests exceptions are properly handled changing config flags.
    """
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_config_flags_exception"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    # Simulate some time has passed for HomeAssistant to invoke
    # update for components
    async_fire_time_changed(hass, dt.utcnow() + timedelta(hours=1))
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'switch', unique_id
    )

    # Setup the config flag to a known state, basically the opposite of
    # what we expect after the service call with simulated exception
    setup_call = (
        SERVICE_TURN_ON if expected_state == 'on' else SERVICE_TURN_OFF
    )
    await hass.services.async_call(
        SWITCH_DOMAIN,
        setup_call,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Simulate an exception when setting the config flag.
    # `attrgetter` is used to handle nested attribute names (dot notation) -
    # `getattr` only works for single level attributes
    attrgetter(expected_call)(
        mock_g90alarm.return_value
    ).side_effect = simulated_exception

    # Attempt to set the switch for the config flag to the desired state
    await hass.services.async_call(
        SWITCH_DOMAIN,
        service_call,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Verify the switch for the config flag is in the expected state (i.e. did
    # not change due to the exception)
    switch_state = hass.states.get(entity_id)
    assert switch_state is not None
    assert switch_state.state == expected_state


@pytest.mark.parametrize(
    "device_name,unique_id,service_call,expected_call,expected_value",
    [
        pytest.param(
            "Dummy switch 1", "dummy_guid_switch_0_1",
            SERVICE_TURN_ON, 'turn_on', 'on',
            id="Switch turn on"
        ),
        pytest.param(
            "Dummy switch 1", "dummy_guid_switch_0_1",
            SERVICE_TURN_OFF, 'turn_off', 'off',
            id="Switch turn off"
        ),
        pytest.param(
            "Dummy switch 2 multi-node#1", "dummy_guid_switch_1_1",
            SERVICE_TURN_ON, 'turn_on', 'on',
            id="Multi-node switch turn on"
        ),
        pytest.param(
            "Dummy switch 2 multi-node#2", "dummy_guid_switch_1_2",
            SERVICE_TURN_OFF, 'turn_off', 'off',
            id="Multi-node switch turn off"
        ),
    ]
)
# pylint: disable=too-many-arguments,too-many-positional-arguments
async def test_device(
    device_name: str, unique_id: str, service_call: str,
    expected_call: str, expected_value: str,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Test that calling the switch service (turn_on or turn_off) for a given
    entity results in the corresponding method being called on the correct
    device instance.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_switch"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    # Simulate some time has passed for HomeAssistant to invoke
    # update for components
    async_fire_time_changed(hass, dt.utcnow() + timedelta(hours=1))
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'switch', unique_id
    )

    # Call the switch service to turn the device on or off
    await hass.services.async_call(
        SWITCH_DOMAIN,
        service_call,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    device = next(
        iter(
            dev for dev in await mock_g90alarm.get_devices()
            if dev.name == device_name
        )
    )
    assert device is not None, (
        f"Device '{device_name}' not found"
    )
    getattr(device, expected_call).assert_called_once()

    switch_state = hass.states.get(entity_id)
    assert switch_state is not None
    assert switch_state.state == expected_value


@pytest.mark.parametrize(
    "entity_id,restored_state,expected_state,simulated_exception,"
    "expected_call,expected_args,expect_no_call", [
        pytest.param(
            "switch.dummy_guid_simulate_alerts_from_history", "on", "on",
            None,
            'start_simulating_alerts_from_history', (), False,
            id="Enabled simulating alerts from history"
        ),
        pytest.param(
            "switch.dummy_guid_simulate_alerts_from_history", "on", "off",
            G90Error('dummy exception'),
            'start_simulating_alerts_from_history', (), False,
            id="Exception with enabled simulating alerts from history"
        ),
        pytest.param(
            "switch.dummy_guid_simulate_alerts_from_history", "off", "off",
            None,
            'stop_simulating_alerts_from_history', (), True,
            id="Disabled simulating alerts from history"
        ),
        pytest.param(
            "switch.dummy_guid_sms_alert_when_armed", "on", "on",
            None,
            None, ('sms_alert_when_armed', True), False,
            id="Enabled SMS alert when armed"
        ),
        pytest.param(
            "switch.dummy_guid_sms_alert_when_armed", "off", "off",
            None,
            None, ('sms_alert_when_armed', False), False,
            id="Disabled SMS alert when armed"
        ),
    ]
)
async def test_config_flags_restore_state(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT,
    entity_id: str, restored_state: str, expected_state: str,
    simulated_exception: Optional[Exception],
    expected_call: Optional[str],
    expected_args: tuple[G90AlertConfigFlags | str, bool],
    expect_no_call: bool,
) -> None:
    """
    Verifies that states are restored on startup for the switch entities having
    that functionality.
    """
    # pylint: disable=too-many-arguments,too-many-positional-arguments

    # Simulate restored state for the entity
    mock_restore_cache(hass, [State(entity_id, restored_state)])

    if simulated_exception and expected_call:
        # Setup the config flag to raise an exception when being restored
        attrgetter(expected_call)(
            mock_g90alarm.return_value
        ).side_effect = simulated_exception

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_restore_state"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    # Verify the entity state was restored correctly
    switch_state = hass.states.get(entity_id)
    assert switch_state is not None
    assert switch_state.state == expected_state

    # Verify the configuration has been restored correctly
    if expected_call is None:
        # `expected_args` are interpreted as property name and value to
        # verify
        (prop, value) = expected_args
        assert getattr(mock_g90alarm.return_value, str(prop)) == value
        return

    if expect_no_call:
        # Verify the expected method was not called
        getattr(
            mock_g90alarm.return_value, expected_call
        ).assert_not_called()
    else:
        # Verify the expected method was called with expected arguments
        mock_g90alarm.return_value.assert_has_calls([
            getattr(call, expected_call)(*expected_args),
        ])


@pytest.mark.parametrize(
    "unique_id,service,field,value",
    [
        pytest.param(
            "dummy_guid_ap_enabled", "turn_on", "ap_enabled", True,
            id="AP enabled"
        ),
        pytest.param(
            "dummy_guid_ap_enabled", "turn_off", "ap_enabled", False,
            id="AP disabled"
        ),
        pytest.param(
            "dummy_guid_gprs_enabled", "turn_on", "gprs_enabled", True,
            id="GPRS enabled"
        ),
        pytest.param(
            "dummy_guid_gprs_enabled", "turn_off", "gprs_enabled", False,
            id="GPRS disabled"
        ),
    ],
)
class TestNetConfigSwitchEntities:
    """
    Tests for network configuration switch entities.
    """
    # pylint: disable=too-many-positional-arguments,too-many-arguments
    async def test_net_config_switch_entities(
        self,
        unique_id: str, service: str, field: str, value: bool,
        hass: HomeAssistant, mock_g90alarm: AlarmMockT
    ) -> None:
        """
        Tests network config switch entities can be toggled correctly.
        """
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={'ip_addr': 'dummy-ip'},
            options={},
            entry_id="test_net_config_switch"
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        entity_id = hass_get_entity_id_by_unique_id(hass, 'switch', unique_id)

        # Toggle the switch
        await hass.services.async_call(
            SWITCH_DOMAIN,
            service,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.async_block_till_done()

        # Verify save was called
        (await mock_g90alarm.return_value.net_config()).save.assert_called()
        # Verify the value was set correctly
        assert getattr(
            await mock_g90alarm.return_value.net_config(), field
        ) == value

    # pylint: disable=too-many-positional-arguments,too-many-arguments
    async def test_net_config_switch_data_change(
        self,
        unique_id: str,
        service: str,  # pylint: disable=unused-argument
        field: str, value: bool,
        hass: HomeAssistant, mock_g90alarm: AlarmMockT
    ) -> None:
        """
        Tests data change propagation in network configuration.
        """
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={'ip_addr': 'dummy-ip'},
            options={},
            entry_id="test_net_config_switch_data_change"
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        # Simulate data update
        setattr(await mock_g90alarm.return_value.net_config(), field, value)

        # Simulate some time has passed for HomeAssistant to invoke
        # update for coordinators and entities
        async_fire_time_changed(hass, dt.utcnow() + timedelta(hours=1))
        await hass.async_block_till_done()

        # Verify the entity state was updated correctly
        entity_id = hass_get_entity_id_by_unique_id(hass, 'switch', unique_id)
        entity = hass.states.get(entity_id)
        assert entity is not None
        assert entity.state == STATE_ON if value else STATE_OFF


async def test_net_config_switch_exception(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests network config switch entities handle exceptions correctly.
    """
    (
        await mock_g90alarm.return_value.net_config()
    ).save.side_effect = G90Error('dummy exception')

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_net_config_switch_exception"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'switch', 'dummy_guid_ap_enabled'
    )

    # Attempt to toggle switch, which should not raise an exception
    await hass.services.async_call(
        SWITCH_DOMAIN,
        'turn_on',
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify save was called despite exception
    (await mock_g90alarm.return_value.net_config()).save.assert_called()
