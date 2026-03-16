# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ilia Sotnikov
"""
Tests for the data update coordinator.
"""
from __future__ import annotations

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from pytest_homeassistant_custom_component.common import MockConfigEntry

from pyg90alarm import G90TimeoutError

from custom_components.gs_alarm.const import DOMAIN, SCAN_INTERVAL
from custom_components.gs_alarm.coordinator import GsAlarmCoordinator

from .conftest import AlarmMockT


async def test_coordinator_sets_retry_after_on_timeout(
    hass: HomeAssistant,
    mock_g90alarm: AlarmMockT,
) -> None:
    """
    Verify that a timeout during data update results in `UpdateFailed`
    with `retry_after` hint set so Home Assistant will retry later.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"ip_addr": "dummy-ip"},
        entry_id="test",
    )

    coordinator = GsAlarmCoordinator(
        hass,
        config_entry,
        mock_g90alarm.return_value,
    )

    # Ensure `self.data.host_info.host_guid` is populated so the error
    # message formatting in the timeout handler works as expected.
    await coordinator.init_essential_data()

    # Simulate timeout on the next update.
    mock_g90alarm.return_value.get_sensors.side_effect = G90TimeoutError(
        "simulated timeout"
    )

    with pytest.raises(UpdateFailed) as ctx:
        await coordinator.update()

    exc = ctx.value
    # `retry_after` should be set so the coordinator schedules a retry.
    assert isinstance(exc.retry_after, float)
    assert exc.retry_after == SCAN_INTERVAL.total_seconds()
    assert "Timeout updating panel" in str(exc)
