# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Test for selects in the custom component.
"""
from __future__ import annotations
import pytest

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_ENTITY_ID,
)
from homeassistant.components.select import (
    ATTR_OPTION,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)

from pyg90alarm import (
    G90SensorAlertModes, G90Error,
    G90APNAuth, G90VolumeLevel, G90SpeechLanguage,
)

from custom_components.gs_alarm.const import DOMAIN
from .conftest import AlarmMockT, hass_get_entity_id_by_unique_id


@pytest.mark.parametrize(
    "unique_id,service_call,option,expected_value",
    [
        pytest.param(
            "dummy_guid_sensor_0_alert_mode", SERVICE_SELECT_OPTION,
            "alert_always",
            G90SensorAlertModes.ALERT_ALWAYS,
            id="Alert always"
        ),
        pytest.param(
            "dummy_guid_sensor_0_alert_mode", SERVICE_SELECT_OPTION,
            "alert_when_away",
            G90SensorAlertModes.ALERT_WHEN_AWAY,
            id="Alert when away"
        ),
        pytest.param(
            "dummy_guid_sensor_0_alert_mode", SERVICE_SELECT_OPTION,
            "alert_when_away_and_home",
            G90SensorAlertModes.ALERT_WHEN_AWAY_AND_HOME,
            id="Alert when away and home"
        ),
    ],
)
# pylint: disable=too-many-positional-arguments,too-many-arguments
async def test_sensor_alert_modes(
    unique_id: str, service_call: str,
    option: str,
    expected_value: G90SensorAlertModes,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests sensor alert modes are set correctly thru corresponding select.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_sensor_alert_modes"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(hass, 'select', unique_id)

    # Change the sensor alert mode thru state of corresponding select
    await hass.services.async_call(
        SELECT_DOMAIN,
        service_call,
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: option},
        blocking=True,
    )

    # Verify the sensor alert mode was set correctly
    sensor = (await mock_g90alarm.return_value.get_sensors())[0]
    sensor.set_alert_mode.assert_called_once_with(expected_value)


async def test_sensor_alert_modes_exception(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests sensor alert modes are set correctly thru corresponding select.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_sensor_alert_modes_exception"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    sensor = (await mock_g90alarm.return_value.get_sensors())[0]
    # Simulate an exception when setting the sensor alert mode
    sensor.set_alert_mode.side_effect = G90Error('dummy exception')

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'select', 'dummy_guid_sensor_0_alert_mode'
    )

    # Attempt to change the alert mode of the sensor, which shouldn't raise
    # an exception
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_OPTION: 'alert_always'
        },
        blocking=True,
    )

    # Verify the switch for the sensor mode is still in previous state
    dummy_sensor_1_alert_mode = hass.states.get(entity_id)
    assert dummy_sensor_1_alert_mode is not None
    assert dummy_sensor_1_alert_mode.state == 'alert_when_away'


@pytest.mark.parametrize(
    "unique_id,option,field,value",
    [
        pytest.param(
            "dummy_guid_apn_auth", "none",
            "apn_auth", G90APNAuth.NONE,
            id="APN auth - none"
        ),
        pytest.param(
            "dummy_guid_apn_auth", "pap",
            "apn_auth", G90APNAuth.PAP,
            id="APN auth - PAP"
        ),
        pytest.param(
            "dummy_guid_apn_auth", "chap",
            "apn_auth", G90APNAuth.CHAP,
            id="APN auth - CHAP"
        ),
        pytest.param(
            "dummy_guid_apn_auth", "pap_or_chap",
            "apn_auth", G90APNAuth.PAP_OR_CHAP,
            id="APN auth - PAP or CHAP"
        ),
    ],
)
# pylint: disable=too-many-positional-arguments,too-many-arguments
async def test_net_config_select_entities(
    unique_id: str, option: str, field: str, value: G90APNAuth,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests network config select entities can be set correctly.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_net_config_select"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(hass, 'select', unique_id)

    # Set the option
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: option},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify save was called
    (await mock_g90alarm.return_value.net_config()).save.assert_called()
    # Verify the value was set correctly
    assert getattr(
        await mock_g90alarm.return_value.net_config(), field
    ) == value


@pytest.mark.parametrize(
    "unique_id,option,field,value",
    [
        pytest.param(
            "dummy_guid_alarm_volume_level", "mute",
            "alarm_volume_level", G90VolumeLevel.MUTE,
            id="Alarm volume - mute"
        ),
        pytest.param(
            "dummy_guid_alarm_volume_level", "low",
            "alarm_volume_level", G90VolumeLevel.LOW,
            id="Alarm volume - low"
        ),
        pytest.param(
            "dummy_guid_alarm_volume_level", "high",
            "alarm_volume_level", G90VolumeLevel.HIGH,
            id="Alarm volume - high"
        ),
        pytest.param(
            "dummy_guid_speech_volume_level", "low",
            "speech_volume_level", G90VolumeLevel.LOW,
            id="Speech volume - low"
        ),
        pytest.param(
            "dummy_guid_key_tone_volume_level", "high",
            "key_tone_volume_level", G90VolumeLevel.HIGH,
            id="Key tone volume - high"
        ),
        pytest.param(
            "dummy_guid_ring_volume_level", "mute",
            "ring_volume_level", G90VolumeLevel.MUTE,
            id="Ring volume - mute"
        ),
        pytest.param(
            "dummy_guid_speech_language", "english_female",
            "speech_language", G90SpeechLanguage.ENGLISH_FEMALE,
            id="Speech language - English female"
        ),
        pytest.param(
            "dummy_guid_speech_language", "none",
            "speech_language", G90SpeechLanguage.NONE,
            id="Speech language - None"
        ),
    ],
)
# pylint: disable=too-many-positional-arguments,too-many-arguments
async def test_host_config_select_entities(
    unique_id: str, option: str,
    field: str, value: G90VolumeLevel | G90SpeechLanguage,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests host config select entities can be set correctly.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_host_config_select"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(hass, 'select', unique_id)

    # Set the option
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: option},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify save was called
    (await mock_g90alarm.return_value.host_config()).save.assert_called()
    # Verify the value was set correctly
    assert getattr(
        await mock_g90alarm.return_value.host_config(), field
    ) == value
