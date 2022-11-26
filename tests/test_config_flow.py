"""
tbd
"""
import pytest

from homeassistant.data_entry_flow import FlowResultType
from homeassistant.config_entries import ConfigEntry

from custom_components.gs_alarm.const import DOMAIN


@pytest.mark.g90discovery(result=[
    {
        'guid': 'Dummy guid',
        'host': 'dummy-discovered-host',
        'port': 4321,
    }
])
async def test_config_flow_discovered_devices(hass, mock_g90alarm):
    """
    tbd
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )

    assert result['step_id'] == 'confirm'
    assert result['type'] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        flow_id=result['flow_id'],
        user_input={},
    )
    assert result['type'] == FlowResultType.CREATE_ENTRY
    assert isinstance(result['result'], ConfigEntry)
    assert result['result'].domain == DOMAIN
    # Port is ignored
    mock_g90alarm.assert_called_with(host='dummy-discovered-host')


async def test_config_flow_manual_device(hass, mock_g90alarm):
    """
    tbd
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )

    assert result['step_id'] == 'confirm'
    assert result['type'] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        flow_id=result['flow_id'],
        user_input={},
    )
    assert result['type'] == FlowResultType.FORM
    assert result['step_id'] == 'custom_host'

    result = await hass.config_entries.flow.async_configure(
        flow_id=result['flow_id'],
        user_input={'ip_addr': 'dummy-manual-host'},
    )
    assert result['type'] == FlowResultType.CREATE_ENTRY
    assert isinstance(result['result'], ConfigEntry)
    assert result['result'].domain == DOMAIN
    # Port is ignored
    mock_g90alarm.assert_called_with(host='dummy-manual-host')


# pylint: disable=unused-argument
async def test_config_flow_manual_device_no_ip_addr(hass, mock_g90alarm):
    """
    tbd
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )

    assert result['step_id'] == 'confirm'
    assert result['type'] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        flow_id=result['flow_id'],
        user_input={},
    )
    assert result['type'] == FlowResultType.FORM
    assert result['step_id'] == 'custom_host'

    result = await hass.config_entries.flow.async_configure(
        flow_id=result['flow_id'],
        user_input={'ip_addr': ''},
    )
    assert result['type'] == FlowResultType.FORM
    assert result['errors']
