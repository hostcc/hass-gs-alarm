
"""
Test for selects in the custom component.
"""
from __future__ import annotations
import pytest

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_ENTITY_ID,
)
from homeassistant.components.select import (
    ATTR_OPTION,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)

from pyg90alarm import G90SensorAlertModes, G90Error

from custom_components.gs_alarm.const import DOMAIN
from .conftest import AlarmMockT, hass_get_entity_id_by_unique_id


@pytest.mark.parametrize(
    "unique_id,service_call,option,expected_value",
    [
        pytest.param(
            "dummy_guid_sensor_0_alert_mode", SERVICE_SELECT_OPTION,
            "alert_always",
            G90SensorAlertModes.ALERT_ALWAYS,
            id="Alert always"
        ),
        pytest.param(
            "dummy_guid_sensor_0_alert_mode", SERVICE_SELECT_OPTION,
            "alert_when_away",
            G90SensorAlertModes.ALERT_WHEN_AWAY,
            id="Alert when away"
        ),
        pytest.param(
            "dummy_guid_sensor_0_alert_mode", SERVICE_SELECT_OPTION,
            "alert_when_away_and_home",
            G90SensorAlertModes.ALERT_WHEN_AWAY_AND_HOME,
            id="Alert when away and home"
        ),
    ],
)
# pylint: disable=too-many-arguments
async def test_sensor_alert_modes(
    unique_id: str, service_call: str,
    option: str,
    expected_value: G90SensorAlertModes,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests sensor alert modes are set correctly thru corresponding select.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_sensor_alert_modes"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(hass, 'select', unique_id)

    # Change the sensor alert mode thru state of corresponding select
    await hass.services.async_call(
        SELECT_DOMAIN,
        service_call,
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: option},
        blocking=True,
    )

    # Verify the sensor alert mode was set correctly
    sensor = mock_g90alarm.return_value.get_sensors.return_value[0]
    sensor.set_alert_mode.assert_called_once_with(expected_value)


async def test_sensor_alert_modes_exception(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests sensor alert modes are set correctly thru corresponding select.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_sensor_alert_modes_exception"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    sensor = mock_g90alarm.return_value.get_sensors.return_value[0]
    # Simulate an exception when setting the sensor alert mode
    sensor.set_alert_mode.side_effect = G90Error('dummy exception')

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'select', 'dummy_guid_sensor_0_alert_mode'
    )

    # Attempt to change the alert mode of the sensor, which shouldn't raise
    # an exception
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_OPTION: 'alert_always'
        },
        blocking=True,
    )

    # Verify the switch for the sensor mode is still in previous state
    dummy_sensor_1_alert_mode = hass.states.get(entity_id)
    assert dummy_sensor_1_alert_mode is not None
    assert dummy_sensor_1_alert_mode.state == 'alert_when_away'
