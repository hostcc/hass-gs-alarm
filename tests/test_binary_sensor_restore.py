# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ilia Sotnikov
"""
Tests for binary sensor state restoration at startup.
"""
import pytest

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
)

from homeassistant.core import HomeAssistant, State

from custom_components.gs_alarm.const import (
    DOMAIN,
    CONF_RESTORE_STATE_AT_STARTUP,
)
from .conftest import (
    AlarmMockT, hass_get_state_by_unique_id, allow_callbacks_to_complete,
)


MAIN_SENSOR_ENTITY_ID = 'binary_sensor.dummy_guid_dummy_sensor'
TAMPERED_SENSOR_ENTITY_ID = 'binary_sensor.dummy_guid_dummy_sensor_tampered'
MAIN_SENSOR_UNIQUE_ID = 'dummy_guid_sensor_0'
TAMPERED_SENSOR_UNIQUE_ID = 'dummy_guid_sensor_0_tampered'
LOW_BATTERY_SENSOR_ENTITY_ID = (
    'binary_sensor.dummy_guid_dummy_sensor_low_battery'
)
LOW_BATTERY_SENSOR_UNIQUE_ID = 'dummy_guid_sensor_0_low_battery'


@pytest.mark.usefixtures('mock_g90alarm')
@pytest.mark.parametrize(
    'entity_id,unique_id,restored_state,expected_state',
    [
        pytest.param(
            MAIN_SENSOR_ENTITY_ID, MAIN_SENSOR_UNIQUE_ID, 'on', 'on',
            id='main_sensor_on',
        ),
        pytest.param(
            MAIN_SENSOR_ENTITY_ID, MAIN_SENSOR_UNIQUE_ID, 'off', 'off',
            id='main_sensor_off',
        ),
        pytest.param(
            TAMPERED_SENSOR_ENTITY_ID, TAMPERED_SENSOR_UNIQUE_ID, 'on', 'on',
            id='tampered_attribute_on',
        ),
    ],
)
# pylint: disable=too-many-positional-arguments,too-many-arguments
async def test_binary_sensor_restore_state_on_startup(
    hass: HomeAssistant,
    entity_id: str, unique_id: str,
    restored_state: str, expected_state: str,
) -> None:
    """
    Verifies last HA state is restored when the option is enabled.
    """
    mock_restore_cache(hass, [State(entity_id, restored_state)])

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id='test_binary_sensor_restore',
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', unique_id
    )
    assert sensor_state.state == expected_state


@pytest.mark.usefixtures('mock_g90alarm')
async def test_binary_sensor_restore_state_disabled(
    hass: HomeAssistant,
) -> None:
    """
    Verifies restored state is ignored when restore_state_at_startup is off.
    """
    mock_restore_cache(hass, [State(MAIN_SENSOR_ENTITY_ID, 'on')])

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={CONF_RESTORE_STATE_AT_STARTUP: False},
        entry_id='test_binary_sensor_restore_disabled',
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    )
    assert sensor_state.state == 'off'


async def test_binary_sensor_restore_cleared_on_panel_update(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT,
) -> None:
    """
    Verifies restored state is replaced after a live panel state callback.
    """
    mock_restore_cache(hass, [State(MAIN_SENSOR_ENTITY_ID, 'on')])

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id='test_binary_sensor_restore_cleared',
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    )
    assert sensor_state.state == 'on'

    await mock_g90alarm.return_value.on_sensor_activity(
        0, 'Dummy sensor', False
    )
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    )
    assert sensor_state.state == 'off'


async def test_binary_sensor_restore_state_on_reload(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT,
) -> None:
    """
    Verifies restored state survives integration reload without a new callback.
    """
    mock_restore_cache(hass, [State(MAIN_SENSOR_ENTITY_ID, 'on')])

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id='test_binary_sensor_restore_reload',
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    await mock_g90alarm.return_value.on_sensor_activity(
        0, 'Dummy sensor', True
    )
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    )
    assert sensor_state.state == 'on'

    await hass.config_entries.async_reload(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    )
    assert sensor_state.state == 'on'


async def test_binary_sensor_restore_state_independent_across_entities(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT,
) -> None:
    """
    Verifies restored state on one sensor entity does not affect others.
    """
    mock_restore_cache(hass, [
        State(MAIN_SENSOR_ENTITY_ID, 'on'),
        State(TAMPERED_SENSOR_ENTITY_ID, 'on'),
        State(LOW_BATTERY_SENSOR_ENTITY_ID, 'off'),
    ])

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id='test_binary_sensor_restore_independent',
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    ).state == 'on'
    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', TAMPERED_SENSOR_UNIQUE_ID
    ).state == 'on'
    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', LOW_BATTERY_SENSOR_UNIQUE_ID
    ).state == 'off'

    await mock_g90alarm.return_value.on_sensor_activity(
        0, 'Dummy sensor', False
    )
    await allow_callbacks_to_complete(hass)

    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', MAIN_SENSOR_UNIQUE_ID
    ).state == 'off'
    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', TAMPERED_SENSOR_UNIQUE_ID
    ).state == 'on'
    assert hass_get_state_by_unique_id(
        hass, 'binary_sensor', LOW_BATTERY_SENSOR_UNIQUE_ID
    ).state == 'off'
