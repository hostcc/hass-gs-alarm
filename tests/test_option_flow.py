"""
Tests for option (configure) flow for the custom component.
"""
from unittest.mock import PropertyMock

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)

from pyg90alarm import G90Alarm
from custom_components.gs_alarm.const import DOMAIN


async def test_config_flow_options(
    hass: HomeAssistant, mock_g90alarm: G90Alarm
) -> None:
    """
    Tests options (configure) flow for the component with correct inputs.
    """
    # Instantiate the component into HomeAssistant, required for its options
    # flow handler to be registered
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    # Initial step
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id,
        context={"source": "user"},
    )
    # Verify it results in form
    assert result['step_id'] == 'init'
    assert result['type'] == FlowResultType.FORM

    # Submission step configuring the single mocked sensor to be disabled (by
    # its index) and enabling `SMS alert only when armed`
    result = await hass.config_entries.options.async_configure(
        flow_id=result['flow_id'],
        user_input={
            'sms_alert_when_armed': True,
            'disabled_sensors': ['0'],
            'simulate_alerts_from_history': True,
        },
    )
    # Verify it results in (re)creating corresponding entry in HomeAssistant
    assert result['type'] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    # Verify the sensor has to its `set_enabled()` method invoked with proper
    # arguments
    (
        mock_g90alarm.return_value
        .get_sensors.return_value[0]
        .set_enabled
    ).assert_called_once_with(False)

    # Verify the value of the `sms_alert_when_armed` property of `G90Alarm()`
    # instance
    assert mock_g90alarm.return_value.sms_alert_when_armed

    # Verify simulating device alerts from history has been started
    (mock_g90alarm.return_value
        .start_simulating_alerts_from_history.assert_called())


async def test_config_flow_options_unsupported_disable(
    hass: HomeAssistant, mock_g90alarm: G90Alarm
) -> None:
    """
    Tests options (configure) flow for the component where sensor attempted to
    disable and it isn't supported.
    """
    # Instantiate the component into HomeAssistant, required for its options
    # flow handler to be registered
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    # Initial step
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id,
        context={"source": "user"},
    )
    # Verify it results in form
    assert result['step_id'] == 'init'
    assert result['type'] == FlowResultType.FORM

    # Simulate the sensor doesn't support enabling/disabling
    (
        type(mock_g90alarm.return_value.get_sensors.return_value[0])
        .supports_enable_disable
    ) = PropertyMock(return_value=False)

    # Submission step configuring the single mocked sensor to be disabled
    result = await hass.config_entries.options.async_configure(
        flow_id=result['flow_id'],
        user_input={'disabled_sensors': ['0']},
    )
    # Verify it results in (re)creating corresponding entry in HomeAssistant
    assert result['type'] == FlowResultType.CREATE_ENTRY
    # Verify disabling the sensor has not been called
    (
        mock_g90alarm.return_value
        .get_sensors.return_value[0]
        .set_enabled
    ).assert_not_called()
