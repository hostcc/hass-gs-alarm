# SPDX-License-Identifier: MIT
# Copyright (c) 2021 Ilia Sotnikov
"""
Tests for switches from the custom component.
"""
from __future__ import annotations
from datetime import timedelta
import pytest

from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    MockConfigEntry,
)

from homeassistant.core import HomeAssistant
from homeassistant.util import dt
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
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
    "unique_id,service_call,expected_flag,expected_value",
    [
        pytest.param(
            "dummy_guid_alert_config_flag_ac_power_failure", SERVICE_TURN_ON,
            G90AlertConfigFlags.AC_POWER_FAILURE, True,
            id="AC power failure enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_ac_power_failure", SERVICE_TURN_OFF,
            G90AlertConfigFlags.AC_POWER_FAILURE, False,
            id="AC power failure disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_wifi_available", SERVICE_TURN_ON,
            G90AlertConfigFlags.WIFI_AVAILABLE, True,
            id="WiFi available enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_wifi_available", SERVICE_TURN_OFF,
            G90AlertConfigFlags.WIFI_AVAILABLE, False,
            id="WiFi available disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_wifi_unavailable", SERVICE_TURN_ON,
            G90AlertConfigFlags.WIFI_UNAVAILABLE, True,
            id="WiFi unavailable enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_wifi_unavailable", SERVICE_TURN_OFF,
            G90AlertConfigFlags.WIFI_UNAVAILABLE, False,
            id="WiFi unavailable disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_door_open", SERVICE_TURN_ON,
            G90AlertConfigFlags.DOOR_OPEN, True,
            id="Door open enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_door_open", SERVICE_TURN_OFF,
            G90AlertConfigFlags.DOOR_OPEN, False,
            id="Door open disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_door_close", SERVICE_TURN_ON,
            G90AlertConfigFlags.DOOR_CLOSE, True,
            id="Door close enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_door_close", SERVICE_TURN_OFF,
            G90AlertConfigFlags.DOOR_CLOSE, False,
            id="Door close disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_sms_push", SERVICE_TURN_ON,
            G90AlertConfigFlags.SMS_PUSH, True,
            id="SMS push enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_sms_push", SERVICE_TURN_OFF,
            G90AlertConfigFlags.SMS_PUSH, False,
            id="SMS push disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_arm_disarm", SERVICE_TURN_ON,
            G90AlertConfigFlags.ARM_DISARM, True,
            id="Arm disarm enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_arm_disarm", SERVICE_TURN_OFF,
            G90AlertConfigFlags.ARM_DISARM, False,
            id="Arm disarm disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_host_low_voltage", SERVICE_TURN_ON,
            G90AlertConfigFlags.HOST_LOW_VOLTAGE, True,
            id="Host low voltage enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_host_low_voltage", SERVICE_TURN_OFF,
            G90AlertConfigFlags.HOST_LOW_VOLTAGE, False,
            id="Host low voltage disabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_sensor_low_voltage", SERVICE_TURN_ON,
            G90AlertConfigFlags.SENSOR_LOW_VOLTAGE, True,
            id="Sensor low voltage enabled"
        ),
        pytest.param(
            "dummy_guid_alert_config_flag_sensor_low_voltage",
            SERVICE_TURN_OFF,
            G90AlertConfigFlags.SENSOR_LOW_VOLTAGE, False,
            id="Sensor low voltage disabled"
        ),
    ],
)
# pylint: disable=too-many-positional-arguments,too-many-arguments
async def test_alert_config_flags(
    unique_id: str, service_call: str,
    expected_flag: G90AlertConfigFlags, expected_value: bool,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests alert config flags are set correctly thru corresponding switches.
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

    # Change the alert config flag thru state of corresponding switch
    await hass.services.async_call(
        SWITCH_DOMAIN,
        service_call,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Verify the alert config flag was set correctly
    alert_config = mock_g90alarm.return_value.alert_config
    alert_config.set_flag.assert_called_once_with(
        expected_flag, expected_value
    )


async def test_alert_config_flags_exception(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests exceptions are properly handled changing alert config flags.
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

    # Simulate an exception when setting the alert flags
    mock_g90alarm.return_value.alert_config.set_flag.side_effect = G90Error(
        'dummy exception'
    )

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'switch', 'dummy_guid_alert_config_flag_host_low_voltage'
    )

    # Attempt to turn off the switch for the alert config flag
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Verify the switch for the alert config flag is still on
    alert_config_flag_switch = hass.states.get(entity_id)
    assert alert_config_flag_switch is not None
    assert alert_config_flag_switch.state == 'on'

    # Attempt to turn on the switch - no exception should be raised
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )


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
