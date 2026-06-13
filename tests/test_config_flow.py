# SPDX-License-Identifier: MIT
# Copyright (c) 2022 Ilia Sotnikov
"""
Tests config flow for the custom component.
"""
from unittest.mock import Mock
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.config_entries import ConfigEntry

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gs_alarm.const import (
    DOMAIN,
    CONF_NOTIFICATIONS_PROTOCOL,
    CONF_OPT_NOTIFICATIONS_LOCAL,
    CONF_RESTORE_STATE_AT_STARTUP,
)
from .conftest import AlarmMockT


# Simulate single device discovered
@pytest.mark.g90discovery(result=[
    Mock(
        guid='Dummy guid',
        host='dummy-discovered-host',
        port=4321,
    )
])
async def test_config_flow_discovered_devices(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests config flow with single discovered device.
    """
    # Initial step
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )
    # Verify it results in form
    assert result['step_id'] == 'confirm'
    assert result['type'] == FlowResultType.FORM

    # Submission step
    result = await hass.config_entries.flow.async_configure(
        flow_id=result['flow_id'],
        user_input={},
    )

    # Verify it results in creating entity of proper type/domain
    assert result['type'] == FlowResultType.CREATE_ENTRY
    assert isinstance(result['result'], ConfigEntry)
    assert result['result'].domain == DOMAIN

    # Verify `G90Alarm` has been instantiated with proper host, port is ignored
    mock_g90alarm.assert_called_with(host='dummy-discovered-host')


async def test_config_flow_manual_device(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests config flow with no discovered and single manually added device.
    """
    # Initial step
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )
    # Verify it results in form
    assert result['step_id'] == 'confirm'
    assert result['type'] == FlowResultType.FORM

    # Submission step confirming to proceed with manual host
    result = await hass.config_entries.flow.async_configure(
        flow_id=result['flow_id'],
        user_input={},
    )
    assert result['type'] == FlowResultType.FORM
    assert result['step_id'] == 'custom_host'

    # Submittion step confirming the manual host
    result = await hass.config_entries.flow.async_configure(
        flow_id=result['flow_id'],
        user_input={'ip_addr': 'dummy-manual-host'},
    )

    # Verify it results in creating entity of proper type/domain
    assert result['type'] == FlowResultType.CREATE_ENTRY
    assert isinstance(result['result'], ConfigEntry)
    assert result['result'].domain == DOMAIN

    # Verify `G90Alarm` has been instantiated with proper host, port is ignored
    mock_g90alarm.assert_called_with(host='dummy-manual-host')


@pytest.mark.usefixtures('mock_g90alarm')
async def test_config_flow_manual_device_no_ip_addr(
    hass: HomeAssistant
) -> None:
    """
    Tests config flow wit manual device and omitted input for its hostname/IP
    address.
    """
    # Initial step
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )
    # Verify it results in form
    assert result['step_id'] == 'confirm'
    assert result['type'] == FlowResultType.FORM

    # Submission step confirming to proceed with manual host
    result = await hass.config_entries.flow.async_configure(
        flow_id=result['flow_id'],
        user_input={},
    )
    assert result['type'] == FlowResultType.FORM
    assert result['step_id'] == 'custom_host'

    # Submission step confirming the manual host providing empty input
    result = await hass.config_entries.flow.async_configure(
        flow_id=result['flow_id'],
        user_input={'ip_addr': ''},
    )
    # Verify it results in form mentioning the error
    assert result['type'] == FlowResultType.FORM
    assert result['errors']


@pytest.mark.usefixtures('mock_g90alarm')
async def test_options_flow_restore_state_at_startup(
    hass: HomeAssistant,
) -> None:
    """
    Verifies restore_state_at_startup option is saved from options flow.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id='test_options_restore_state',
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id
    )
    assert result['type'] == FlowResultType.FORM
    assert result['step_id'] == 'init'

    result = await hass.config_entries.options.async_configure(
        result['flow_id'],
        user_input={
            CONF_NOTIFICATIONS_PROTOCOL: CONF_OPT_NOTIFICATIONS_LOCAL,
            CONF_RESTORE_STATE_AT_STARTUP: False,
        },
    )
    assert result['type'] == FlowResultType.CREATE_ENTRY
    assert result['data'][CONF_RESTORE_STATE_AT_STARTUP] is False
