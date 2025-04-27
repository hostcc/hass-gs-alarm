"""
Tests for option (configure) flow for the custom component.
"""
from unittest.mock import PropertyMock, call
from typing import Dict, Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)

from custom_components.gs_alarm.const import (
    DOMAIN,
    CONF_OPT_NOTTIICATIONS_LOCAL,
    CONF_OPT_NOTTIICATIONS_CLOUD,
    CONF_OPT_NOTTIICATIONS_CLOUD_UPSTREAM
)
from .conftest import AlarmMockT


async def test_config_flow_options(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
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
        context={'source': 'user'},
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


@pytest.mark.parametrize(
    "protocol,user_input,expected_call,expected_kwargs",
    [
        (
            CONF_OPT_NOTTIICATIONS_LOCAL,
            {}, 'use_local_notifications', {},
        ),
        (
            CONF_OPT_NOTTIICATIONS_CLOUD,
            {
                'cloud_local_port': 1234
            },
            'use_cloud_notifications',
            {
                'cloud_local_port': 1234,
                'upstream_host': None,
                'upstream_port': None
            },
        ),
        (
            CONF_OPT_NOTTIICATIONS_CLOUD_UPSTREAM,
            {
                'cloud_local_port': 1234,
                'cloud_upstream_host': 'test-host.example.com',
                'cloud_upstream_port': 5678,
            },
            'use_cloud_notifications',
            {
                'cloud_local_port': 1234,
                'upstream_host': 'test-host.example.com',
                'upstream_port': 5678
            },
        ),
    ],
)
# pylint: disable=too-many-arguments
async def test_config_flow_options_notifications_protocol(
    protocol: str,
    user_input: Dict[str, Any],
    expected_call: str,
    expected_kwargs: Dict[str, Any],
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests options flow for different notification protocols.
    """
    # Instantiate the component into HomeAssistant
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={},
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    # Initial step
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id,
        context={"source": "user"},
    )

    # Verify form
    assert result['step_id'] == 'init'
    assert result['type'] == FlowResultType.FORM

    # Submission step selecting the notifications protocol under test
    result = await hass.config_entries.options.async_configure(
        flow_id=result['flow_id'],
        user_input={
            'sms_alert_when_armed': False,
            'disabled_sensors': [],
            'simulate_alerts_from_history': False,
            'notifications_protocol': protocol,
        },
    )

    # Local notifications won't result in a second step
    if protocol != CONF_OPT_NOTTIICATIONS_LOCAL:
        # Verify it shows cloud configuration form
        assert result['step_id'] == protocol
        assert result['type'] == FlowResultType.FORM

        # Complete cloud configuration
        result = await hass.config_entries.options.async_configure(
            flow_id=result['flow_id'],
            user_input=user_input,
        )

    # Verify it creates entry
    assert result['type'] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    # Since the test simulates initial component setup with no options
    # persisted, the `use_local_notifications()` method will be called
    # first (since local protocol is the default when no options set),
    # and then the method corresponds to selected protocol
    if protocol == CONF_OPT_NOTTIICATIONS_LOCAL:
        # Verify the `use_local_notifications()` method has been called twice,
        # see above for the explanation
        mock_g90alarm.return_value.use_local_notifications.assert_has_calls(
            [call(**expected_kwargs), call(**expected_kwargs)]
        )
    else:
        # Verify the `use_local_notifications()` method has been called earlier
        # than the method corresponds to the selected protocol, i.e. selected
        # method prevails
        assert (
            mock_g90alarm.return_value.mock_calls.index(
                call.use_local_notifications()
            ) < mock_g90alarm.return_value.mock_calls.index(
                getattr(call, expected_call)(**expected_kwargs)
            )
        )


async def test_config_flow_options_unsupported_disable(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
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
