"""
tbd
"""
from datetime import timedelta
from pytest_unordered import unordered

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from homeassistant.util import dt
import homeassistant.helpers.device_registry as dr
import homeassistant.helpers.entity_registry as er

from custom_components.gs_alarm import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.gs_alarm.const import DOMAIN


async def test_setup_unload_and_reload_entry(hass, mock_g90alarm):
    """
    tbd
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={'disabled_sensors': ['Dummy sensor#1']},
        entry_id="test"
    )

    assert await async_setup_entry(hass, config_entry)
    async_fire_time_changed(hass, dt.utcnow() + timedelta(hours=1))
    await hass.async_block_till_done()

    mock_g90alarm.assert_called_once_with(host='dummy-ip')

    integration_devices = dr.async_entries_for_config_entry(
        dr.async_get(hass), config_entry.entry_id
    )
    assert len(integration_devices) == 1
    integration_device_id = integration_devices[0].id

    integration_entities = er.async_entries_for_device(
        er.async_get(hass), integration_device_id
    )
    integration_entity_ids = [x.entity_id for x in integration_entities]
    assert integration_entity_ids == unordered([
        'alarm_control_panel.dummy',
        'binary_sensor.dummy_sensor_1',
        'switch.dummy_switch_1',
        'sensor.gs_alarm_wifi_signal',
        'binary_sensor.gs_alarm_wifi_status',
        'sensor.gs_alarm_gsm_signal',
        'binary_sensor.gs_alarm_gsm_status'
    ])

    assert await async_unload_entry(hass, config_entry)
