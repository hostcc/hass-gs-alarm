"""
tbd
"""
from unittest.mock import PropertyMock

from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)

from custom_components.gs_alarm import (
    async_setup_entry,
)
from custom_components.gs_alarm.const import DOMAIN


async def test_config_flow_options(hass, mock_g90alarm):
    """
    tbd
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
    )
    await async_setup_entry(hass, config_entry)
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id,
        context={"source": "user"},
    )

    result = await hass.config_entries.options.async_configure(
        flow_id=result['flow_id'],
        user_input={
            'sms_alert_when_armed': True,
            'disabled_sensors': ['0']
        },
    )
    assert result['type'] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    (
        mock_g90alarm.return_value
        .get_sensors.return_value[0]
        .set_enabled
    ).assert_called_once_with(False)

    assert mock_g90alarm.return_value.sms_alert_when_armed


async def test_config_flow_options_unsupported_disable(hass, mock_g90alarm):
    """
    tbd
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
    )
    await async_setup_entry(hass, config_entry)
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id,
        context={"source": "user"},
    )

    (
        type(mock_g90alarm.return_value.get_sensors.return_value[0])
        .supports_enable_disable
    ) = PropertyMock(return_value=False)

    result = await hass.config_entries.options.async_configure(
        flow_id=result['flow_id'],
        user_input={'disabled_sensors': ['0']},
    )
    assert result['type'] == FlowResultType.CREATE_ENTRY
    (
        mock_g90alarm.return_value
        .get_sensors.return_value[0]
        .set_enabled
    ).assert_not_called()
