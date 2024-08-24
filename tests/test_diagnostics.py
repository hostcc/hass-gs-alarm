"""
Tests for integration diagnostics.
"""
import pytest
from pytest_unordered import unordered
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)
from pytest_homeassistant_custom_component.typing import (
    ClientSessionGenerator
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
import homeassistant.helpers.device_registry as dr

from pyg90alarm import G90Alarm
from pyg90alarm.exceptions import G90Error

from custom_components.gs_alarm.const import DOMAIN


@pytest.mark.usefixtures('mock_g90alarm')
async def test_diagnostics(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """
    Verifies diagnostics are successfully generated.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-diag"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    # Add `diagnostics` integration
    await async_setup_component(hass, "diagnostics", {})
    await hass.async_block_till_done()

    integration_devices = dr.async_entries_for_config_entry(
        dr.async_get(hass), config_entry.entry_id
    )
    integration_device_id = next(iter(integration_devices)).id

    # Keys expected for the response
    expected_data_keys = unordered([
        'config_entry', 'device_entry', 'alarm_panel'
    ])
    # And its `alarm_panel` nested element
    expected_alarm_panel_keys = unordered([
        'history',
        'host_info',
        'host_status',
        'sensors',
        'devices',
        'alert_config',
        'alert_simulation_task'
    ])

    # Simulate diagnostics download for the config entry
    client = await hass_client()
    response = await client.get(
        f"/api/diagnostics/config_entry/{config_entry.entry_id}"
    )
    # Verify the response
    response_dict = await response.json()
    data = response_dict.get('data')
    assert list(data.keys()) == expected_data_keys
    assert list(data['alarm_panel'].keys()) == expected_alarm_panel_keys

    # Same but for the device
    response = await client.get(
       f"/api/diagnostics/config_entry"
       f"/{config_entry.entry_id}/device/{integration_device_id}"
    )
    response_dict = await response.json()
    data = response_dict.get('data')

    assert list(data.keys()) == expected_data_keys
    assert list(data['alarm_panel'].keys()) == expected_alarm_panel_keys


async def test_diagnostics_exception(
    hass: HomeAssistant, hass_client: ClientSessionGenerator,
    mock_g90alarm: G90Alarm
) -> None:
    """
    Verify the `pyg90alarm` error doesn't lead to diagnostics resulting in
    internal error sent back to the client.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-diag"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await async_setup_component(hass, "diagnostics", {})
    await hass.async_block_till_done()

    # Simulate exception raised from `G90Alarm.history()`
    mock_g90alarm.return_value.history.side_effect = G90Error()

    client = await hass_client()
    response = await client.get(
        f"/api/diagnostics/config_entry/{config_entry.entry_id}"
    )
    # Verify the response
    response_dict = await response.json()
    data = response_dict.get('data')
    assert data == {
        'error':
            "Unable to gather diagnostics data for"
            " panel 'Dummy GUID': G90Error()"
    }
