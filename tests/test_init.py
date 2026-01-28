# SPDX-License-Identifier: MIT
# Copyright (c) 2022 Ilia Sotnikov
"""
Tests for loading/unloading the custom component.
"""
import re
from datetime import timedelta
from unittest.mock import ANY
from pytest_unordered import unordered

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt

from custom_components.gs_alarm.const import DOMAIN
from .conftest import (
    AlarmMockT, hass_get_state_by_unique_id, entry_ids_for_integration_devices
)


# pylint: disable=too-many-locals
async def test_setup_unload_and_reload_entry_afresh(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests the custom integration load and then unloads properly, simulating it
    just been added to HASS with no options persisted previously.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    # Simulate some time has passed for HomeAssistant to invoke
    # update for components
    async_fire_time_changed(hass, dt.utcnow() + timedelta(hours=1))
    await hass.async_block_till_done()

    assert config_entry.title == 'Dummy GUID'

    mock_g90alarm.assert_called_once_with(host='dummy-ip')

    # Verify entities and devices have been added with proper IDs and names
    assert entry_ids_for_integration_devices(hass, config_entry.entry_id) == [
        {
            'device': 'Dummy GUID',
            'device_id': ANY,
            'entities': unordered([{
                'unique_id': 'dummy_guid',
                'entity_id': 'alarm_control_panel.dummy_guid',
                'name': None,
            }, {
                'unique_id': 'dummy_guid_alert_config_flag_ac_power_failure',
                'entity_id':
                    'switch.dummy_guid_alert_config_flag_ac_power_failure',
                'name': 'Alert: AC power failure',
            }, {
                'unique_id': 'dummy_guid_alert_config_flag_ac_power_recover',
                'entity_id':
                    'switch.dummy_guid_alert_config_flag_ac_power_recover',
                'name': 'Alert: AC power recover',
            }, {
                'unique_id': 'dummy_guid_alert_config_flag_arm_disarm',
                'entity_id':
                    'switch.dummy_guid_alert_config_flag_arm_disarm',
                'name': 'Alert: Arm/disarm',
            }, {
                'unique_id': 'dummy_guid_alert_config_flag_host_low_voltage',
                'entity_id':
                    'switch.dummy_guid_alert_config_flag_host_low_voltage',
                'name': 'Alert: Host low voltage',
            }, {
                'unique_id': 'dummy_guid_alert_config_flag_sensor_low_voltage',
                'entity_id':
                    'switch.dummy_guid_alert_config_flag_sensor_low_voltage',
                'name': 'Alert: Sensor low voltage',
            }, {
                'unique_id': 'dummy_guid_alert_config_flag_wifi_available',
                'entity_id':
                    'switch.dummy_guid_alert_config_flag_wifi_available',
                'name': 'Alert: WiFi available',
            }, {
                'unique_id': 'dummy_guid_alert_config_flag_wifi_unavailable',
                'entity_id':
                    'switch.dummy_guid_alert_config_flag_wifi_unavailable',
                'name': 'Alert: WiFi unavailable',
            }, {
                'unique_id': 'dummy_guid_alert_config_flag_door_open',
                'entity_id': 'switch.dummy_guid_alert_config_flag_door_open',
                'name': 'Alert: Door open',
            }, {
                'unique_id': 'dummy_guid_alert_config_flag_door_close',
                'entity_id': 'switch.dummy_guid_alert_config_flag_door_close',
                'name': 'Alert: Door close',
            }, {
                'unique_id': 'dummy_guid_alert_config_flag_sms_push',
                'entity_id': 'switch.dummy_guid_alert_config_flag_sms_push',
                'name': 'Alert: SMS push',
            }, {
                'unique_id': 'dummy_guid_sensor_wifi_signal',
                'entity_id': 'sensor.dummy_guid_wifi_signal',
                'name': 'WiFi signal',
            }, {
                'unique_id': 'dummy_guid_sensor_wifi_status',
                'entity_id': 'binary_sensor.dummy_guid_wifi_status',
                'name': 'WiFi status',
            }, {
                'unique_id': 'dummy_guid_sensor_gsm_signal',
                'entity_id': 'sensor.dummy_guid_gsm_signal',
                'name': 'GSM signal',
            }, {
                'unique_id': 'dummy_guid_sensor_gsm_status',
                'entity_id': 'binary_sensor.dummy_guid_gsm_status',
                'name': 'GSM status',
            }, {
                'unique_id': 'dummy_guid_sensor_last_device_packet',
                'entity_id': 'sensor.dummy_guid_last_device_packet',
                'name': 'Last device packet',
            }, {
                'unique_id': 'dummy_guid_sensor_last_upstream_packet',
                'entity_id': 'sensor.dummy_guid_last_upstream_packet',
                'name': 'Last upstream packet',
            }, {
                'unique_id': 'dummy_guid_new_sensor_type',
                'entity_id': 'select.dummy_guid_new_sensor_type',
                'name': 'New sensor: type',
            }, {
                'unique_id': 'dummy_guid_new_sensor_name',
                'entity_id': 'text.dummy_guid_new_sensor_name',
                'name': 'New sensor: name',
            }, {
                'unique_id': 'dummy_guid_new_sensor_register',
                'entity_id': 'button.dummy_guid_new_sensor_register',
                'name': 'New sensor: register',
            }, {
                'unique_id': 'dummy_guid_new_device_type',
                'entity_id': 'select.dummy_guid_new_device_type',
                'name': 'New relay: type',
            }, {
                'unique_id': 'dummy_guid_new_device_name',
                'entity_id': 'text.dummy_guid_new_device_name',
                'name': 'New relay: name',
            }, {
                'unique_id': 'dummy_guid_new_device_register',
                'entity_id': 'button.dummy_guid_new_device_register',
                'name': 'New relay: register',
            }, {
                'unique_id': 'dummy_guid_simulate_alerts_from_history',
                'entity_id':
                    'switch.dummy_guid_simulate_alerts_from_history',
                'name': 'Simulate alerts from history',
            }, {
                'unique_id': 'dummy_guid_sms_alert_when_armed',
                'entity_id': 'switch.dummy_guid_sms_alert_when_armed',
                'name': 'SMS alerts only when armed',
            }, {
                'unique_id': 'dummy_guid_ap_enabled',
                'entity_id': 'switch.dummy_guid_ap_enabled',
                'name': 'Access point: enabled',
            }, {
                'unique_id': 'dummy_guid_gprs_enabled',
                'entity_id': 'switch.dummy_guid_gprs_enabled',
                'name': 'Cellular: GPRS/3G enabled',
            }, {
                'unique_id': 'dummy_guid_alarm_volume_level',
                'entity_id': 'select.dummy_guid_alarm_volume_level',
                'name': 'Volume: Alarm',
            }, {
                'unique_id': 'dummy_guid_speech_volume_level',
                'entity_id': 'select.dummy_guid_speech_volume_level',
                'name': 'Volume: Speech',
            }, {
                'unique_id': 'dummy_guid_key_tone_volume_level',
                'entity_id': 'select.dummy_guid_key_tone_volume_level',
                'name': 'Volume: Key tone',
            }, {
                'unique_id': 'dummy_guid_ring_volume_level',
                'entity_id': 'select.dummy_guid_ring_volume_level',
                'name': 'Volume: Ring',
            }, {
                'unique_id': 'dummy_guid_speech_language',
                'entity_id': 'select.dummy_guid_speech_language',
                'name': 'Speech: Language',
            }, {
                'unique_id': 'dummy_guid_apn_auth',
                'entity_id': 'select.dummy_guid_apn_auth',
                'name': 'Cellular: APN Authentication',
            }, {
                'unique_id': 'dummy_guid_panel_password',
                'entity_id': 'text.dummy_guid_panel_password',
                'name': 'Panel: Password',
            }, {
                'unique_id': 'dummy_guid_panel_phone_number',
                'entity_id': 'text.dummy_guid_panel_phone_number',
                'name': 'Panel: Phone number',
            }, {
                'unique_id': 'dummy_guid_phone_number_1',
                'entity_id': 'text.dummy_guid_phone_number_1',
                'name': 'Alarm: Phone 1',
            }, {
                'unique_id': 'dummy_guid_phone_number_2',
                'entity_id': 'text.dummy_guid_phone_number_2',
                'name': 'Alarm: Phone 2',
            }, {
                'unique_id': 'dummy_guid_phone_number_3',
                'entity_id': 'text.dummy_guid_phone_number_3',
                'name': 'Alarm: Phone 3',
            }, {
                'unique_id': 'dummy_guid_phone_number_4',
                'entity_id': 'text.dummy_guid_phone_number_4',
                'name': 'Alarm: Phone 4',
            }, {
                'unique_id': 'dummy_guid_phone_number_5',
                'entity_id': 'text.dummy_guid_phone_number_5',
                'name': 'Alarm: Phone 5',
            }, {
                'unique_id': 'dummy_guid_phone_number_6',
                'entity_id': 'text.dummy_guid_phone_number_6',
                'name': 'Alarm: Phone 6',
            }, {
                'unique_id': 'dummy_guid_sms_push_number_1',
                'entity_id': 'text.dummy_guid_sms_push_number_1',
                'name': 'Alarm: SMS push phone 1',
            }, {
                'unique_id': 'dummy_guid_sms_push_number_2',
                'entity_id': 'text.dummy_guid_sms_push_number_2',
                'name': 'Alarm: SMS push phone 2',
            }, {
                'unique_id': 'dummy_guid_ap_password',
                'entity_id': 'text.dummy_guid_ap_password',
                'name': 'Access point: Password',
            }, {
                'unique_id': 'dummy_guid_apn_name',
                'entity_id': 'text.dummy_guid_apn_name',
                'name': 'Cellular: APN Name',
            }, {
                'unique_id': 'dummy_guid_apn_user',
                'entity_id': 'text.dummy_guid_apn_user',
                'name': 'Cellular: APN User',
            }, {
                'unique_id': 'dummy_guid_apn_password',
                'entity_id': 'text.dummy_guid_apn_password',
                'name': 'Cellular: APN Password',
            }, {
                'unique_id': 'dummy_guid_alarm_siren_duration',
                'entity_id': 'number.dummy_guid_alarm_siren_duration',
                'name': 'Duration: Alarm siren',
            }, {
                'unique_id': 'dummy_guid_arm_delay',
                'entity_id': 'number.dummy_guid_arm_delay',
                'name': 'Delay: Arm',
            }, {
                'unique_id': 'dummy_guid_alarm_delay',
                'entity_id': 'number.dummy_guid_alarm_delay',
                'name': 'Delay: Alarm',
            }, {
                'unique_id': 'dummy_guid_backlight_duration',
                'entity_id': 'number.dummy_guid_backlight_duration',
                'name': 'Duration: Backlight',
            }, {
                'unique_id': 'dummy_guid_ring_duration',
                'entity_id': 'number.dummy_guid_ring_duration',
                'name': 'Duration: Ring',
            }, {
                'unique_id': 'dummy_guid_timezone_offset_m',
                'entity_id': 'number.dummy_guid_timezone_offset_m',
                'name': 'Timezone offset',
            }, {
                'unique_id': 'dummy_guid_sensor_cellular_operator',
                'entity_id': 'sensor.dummy_guid_cellular_operator',
                'name': 'Cellular operator',
            }, {
                'unique_id': 'dummy_guid_sensor_gprs_3g_active',
                'entity_id': 'binary_sensor.dummy_guid_gprs_3g_active',
                'name': 'GPRS/3G active',
            }, {
                'unique_id': 'dummy_guid_sensor_battery_voltage',
                'entity_id': 'sensor.dummy_guid_battery_voltage',
                'name': 'Battery voltage',
            },
            ])
        },
        {
            'device': 'Dummy sensor',
            'device_id': ANY,
            'entities': unordered([{
                'unique_id': 'dummy_guid_sensor_0',
                'entity_id': 'binary_sensor.dummy_guid_dummy_sensor',
                'name': None,
            }, {
                'unique_id': 'dummy_guid_sensor_0_enabled',
                'entity_id': 'switch.dummy_guid_dummy_sensor_enabled',
                'name': 'Enabled',
            }, {
                'unique_id': 'dummy_guid_sensor_0_arm_delay',
                'entity_id': 'switch.dummy_guid_dummy_sensor_arm_delay',
                'name': 'Arm delay',
            }, {
                'unique_id': 'dummy_guid_sensor_0_detect_door',
                'entity_id': 'switch.dummy_guid_dummy_sensor_detect_door',
                'name': 'Check active when arming',
            }, {
                'unique_id': 'dummy_guid_sensor_0_door_chime',
                'entity_id': 'switch.dummy_guid_dummy_sensor_door_chime',
                'name': 'Door chime',
            }, {
                'unique_id': 'dummy_guid_sensor_0_independent_zone',
                'entity_id': 'switch.dummy_guid_dummy_sensor_independent_zone',
                'name': 'Disarm from app only',
            }, {
                'unique_id': 'dummy_guid_sensor_0_alert_mode',
                'entity_id': 'select.dummy_guid_dummy_sensor_alert_mode',
                'name': 'Alert mode',
            }, {
                'unique_id': 'dummy_guid_sensor_0_tampered',
                'entity_id': 'binary_sensor.dummy_guid_dummy_sensor_tampered',
                'name': 'Tampered',
            }, {
                'unique_id': 'dummy_guid_sensor_0_low_battery',
                'entity_id':
                    'binary_sensor.dummy_guid_dummy_sensor_low_battery',
                'name': 'Low battery',
            }, {
                'unique_id': 'dummy_guid_sensor_0_open_when_armed',
                'entity_id':
                    'binary_sensor.dummy_guid_dummy_sensor_open_when_armed',
                'name': 'Active when arming',
            }, {
                'unique_id': 'dummy_guid_sensor_0_delete',
                'entity_id': 'button.dummy_guid_dummy_sensor_delete',
                'name': 'Delete',
            }, ])
        },
        {
            'device': 'Dummy switch 1',
            'device_id': ANY,
            'entities': unordered([{
                'unique_id': 'dummy_guid_switch_0_1',
                'entity_id': 'switch.dummy_guid_dummy_switch_1',
                'name': None,
            }, {
                'unique_id': 'dummy_guid_switch_0_delete',
                'entity_id': 'button.dummy_guid_dummy_switch_1_delete',
                'name': 'Delete',
            }, ])
        },
        {
            'device': 'Dummy switch 2 multi-node',
            'device_id': ANY,
            'entities': unordered([{
                'unique_id': 'dummy_guid_switch_1_1',
                'entity_id': 'switch.dummy_guid_dummy_switch_2_multi_node_1',
                'name': 'Dummy switch 2 multi-node#1',
            }, {
                'unique_id': 'dummy_guid_switch_1_2',
                'entity_id': 'switch.dummy_guid_dummy_switch_2_multi_node_2',
                'name': 'Dummy switch 2 multi-node#2',
            }, {
                'unique_id': 'dummy_guid_switch_1_delete',
                'entity_id':
                    'button.dummy_guid_dummy_switch_2_multi_node_1_delete',
                'name': 'Delete',
            }, ])
        },
        {
            'device': 'Dummy switch 3 multi-node',
            'device_id': ANY,
            'entities': unordered([
                {
                    'unique_id': 'dummy_guid_switch_2_1',
                    'entity_id':
                        'switch.dummy_guid_dummy_switch_3_multi_node_1',
                    'name': 'Dummy switch 3 multi-node#1',
                }, {
                    'unique_id': 'dummy_guid_switch_2_2',
                    'entity_id':
                        'switch.dummy_guid_dummy_switch_3_multi_node_2',
                    'name': 'Dummy switch 3 multi-node#2',
                }, {
                    'unique_id': 'dummy_guid_switch_2_delete',
                    'entity_id':
                        'button.dummy_guid_dummy_switch_3_multi_node_1_delete',
                    'name': 'Delete',
                },
            ])
        },
    ]

    # Verify the switches and selects correspond to the binary sensor have
    # proper states
    for platform, unique_id, expected_state in [
        ('switch', 'dummy_guid_sensor_0_enabled', 'on'),
        ('switch', 'dummy_guid_sensor_0_arm_delay', 'off'),
        ('switch', 'dummy_guid_sensor_0_detect_door', 'off'),
        ('switch', 'dummy_guid_sensor_0_door_chime', 'off'),
        ('switch', 'dummy_guid_sensor_0_independent_zone', 'off'),
        ('select', 'dummy_guid_sensor_0_alert_mode', 'alert_when_away'),
    ]:
        entity = hass_get_state_by_unique_id(
            hass, platform, unique_id
        )
        assert entity.state == expected_state

    # Verify binary sensor has expected extra attributes
    dummy_sensor = hass_get_state_by_unique_id(
        hass, 'binary_sensor', 'dummy_guid_sensor_0'
    )

    assert 'wireless' in dummy_sensor.attributes
    assert 'panel_sensor_number' in dummy_sensor.attributes
    assert 'protocol' in dummy_sensor.attributes
    assert 'flags' in dummy_sensor.attributes

    # Verify `G90Alarm` sensors received the HASS entity IDs as `extra_data`
    for sensor in await mock_g90alarm.return_value.get_sensors():
        assert re.search(r'^(sensor|binary_sensor)\..+$', sensor.extra_data)

    mock_g90alarm.return_value.listen_notifications.assert_called_once()

    # Unload the integration
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
