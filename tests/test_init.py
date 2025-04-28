"""
Tests for loading/unloading the custom component.
"""
import re
from datetime import timedelta
from pytest_unordered import unordered

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt
import homeassistant.helpers.device_registry as dr
import homeassistant.helpers.entity_registry as er

from custom_components.gs_alarm.const import DOMAIN
from .conftest import AlarmMockT


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
    # `async_update()` for components
    async_fire_time_changed(hass, dt.utcnow() + timedelta(hours=1))
    await hass.async_block_till_done()

    assert config_entry.title == 'Dummy GUID'

    mock_g90alarm.assert_called_once_with(host='dummy-ip')

    # Verify single device has been added
    integration_devices = dr.async_entries_for_config_entry(
        dr.async_get(hass), config_entry.entry_id
    )
    assert len(integration_devices) == 1
    integration_device_id = integration_devices[0].id

    # Verify corresponding entities (platforms) have been added under the
    # device
    integration_entities = er.async_entries_for_device(
        er.async_get(hass), integration_device_id
    )
    integration_entity_ids = [x.entity_id for x in integration_entities]
    assert integration_entity_ids == unordered([
        'alarm_control_panel.dummy_guid',
        'binary_sensor.dummy_sensor_1',
        'switch.dummy_switch_1',
        'sensor.gs_alarm_wifi_signal',
        'binary_sensor.gs_alarm_wifi_status',
        'sensor.gs_alarm_gsm_signal',
        'binary_sensor.gs_alarm_gsm_status',
        'sensor.gs_alarm_last_device_packet',
        'sensor.gs_alarm_last_upstream_packet',
    ])

    # Verify binary sensor has expected extra attributes
    dummy_sensor_1 = hass.states.get('binary_sensor.dummy_sensor_1')
    assert dummy_sensor_1 is not None
    assert 'wireless' in dummy_sensor_1.attributes
    assert 'panel_sensor_number' in dummy_sensor_1.attributes
    assert 'protocol' in dummy_sensor_1.attributes
    assert 'flags' in dummy_sensor_1.attributes

    # Verify options haven't been propagated to `G90Alarm` instance
    mock_g90alarm.return_value.sms_alert_when_armed.assert_not_called()
    (
        mock_g90alarm.return_value
        .get_sensors.return_value[0]
        .set_enabled
    ).assert_not_called()

    # Verify `G90Alarm` sensors received the HASS entity IDs as `extra_data`
    for sensor in await mock_g90alarm.return_value.get_sensors():
        assert re.search(r'^(sensor|binary_sensor)\..+$', sensor.extra_data)

    mock_g90alarm.return_value.listen_notifications.assert_called_once()

    # Unload the integration
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    # Verify the component cleaned up its data upon unloading
    assert not hass.data[DOMAIN]


async def test_setup_entry_with_persisted_options(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests the custom integration loads properly, simulating there are some
    options persisted (integration has been added to HASS and configured).
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={
            'disabled_sensors': ['0'],
            'sms_alert_when_armed': True,
        },
        entry_id="test"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    await hass.async_block_till_done()

    # Verify `G90Alarm` instance has been configured according to integration
    # options
    assert mock_g90alarm.return_value.sms_alert_when_armed is True
    (
        mock_g90alarm.return_value
        .get_sensors.return_value[0]
        .set_enabled
    ).assert_called_once_with(False)
