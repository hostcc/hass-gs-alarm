# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ilia Sotnikov
"""
Tests for the alarm control panel entity.
"""
from unittest.mock import AsyncMock
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_DISARM,
)

from pyg90alarm import G90ArmDisarmTypes

from custom_components.gs_alarm.const import DOMAIN
from .conftest import AlarmMockT, hass_get_state_by_unique_id


@pytest.mark.g90host_status(
    result=G90ArmDisarmTypes.DISARM
)
async def test_alarm_panel_requests_refresh_on_service_calls(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests that alarm panel service calls request coordinator refresh.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test-refresh-calls"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Replace coordinator refresh method with a mock so we can assert calls
    coordinator = config_entry.runtime_data
    coordinator.async_request_refresh = AsyncMock()

    # Prevent real network interaction from G90Alarm methods
    mock_g90alarm.return_value.arm_away = AsyncMock()
    mock_g90alarm.return_value.arm_home = AsyncMock()
    mock_g90alarm.return_value.disarm = AsyncMock()

    panel_state = hass_get_state_by_unique_id(
        hass, 'alarm_control_panel', 'dummy_guid'
    )
    assert panel_state is not None

    # Arm away
    await hass.services.async_call(
        'alarm_control_panel',
        SERVICE_ALARM_ARM_AWAY,
        {'entity_id': panel_state.entity_id},
        blocking=True,
    )

    # Arm home
    await hass.services.async_call(
        'alarm_control_panel',
        SERVICE_ALARM_ARM_HOME,
        {'entity_id': panel_state.entity_id},
        blocking=True,
    )

    # Disarm
    await hass.services.async_call(
        'alarm_control_panel',
        SERVICE_ALARM_DISARM,
        {'entity_id': panel_state.entity_id},
        blocking=True,
    )

    # Verify that coordinator refresh was requested for each service call
    assert coordinator.async_request_refresh.call_count == 3
