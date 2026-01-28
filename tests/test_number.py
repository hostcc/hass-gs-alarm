# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Tests for number entities in the custom component.
"""
from __future__ import annotations
from datetime import timedelta
import pytest

from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    MockConfigEntry,
)

from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.util import dt

from homeassistant.components.number.const import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)

from pyg90alarm import G90Error

from custom_components.gs_alarm.const import DOMAIN
from .conftest import AlarmMockT, hass_get_entity_id_by_unique_id


@pytest.mark.parametrize(
    "unique_id,field,value",
    [
        pytest.param(
            "dummy_guid_alarm_siren_duration", "alarm_siren_duration",
            120,
            id="Alarm siren duration"
        ),
        pytest.param(
            "dummy_guid_arm_delay", "arm_delay",
            30,
            id="Arm delay"
        ),
        pytest.param(
            "dummy_guid_alarm_delay", "alarm_delay",
            45,
            id="Alarm delay"
        ),
        pytest.param(
            "dummy_guid_backlight_duration", "backlight_duration",
            60,
            id="Backlight duration"
        ),
        pytest.param(
            "dummy_guid_ring_duration", "ring_duration",
            10,
            id="Ring duration"
        ),
        pytest.param(
            "dummy_guid_timezone_offset_m", "timezone_offset_m",
            -300,
            id="Timezone offset"
        ),
    ],
)
class TestHostConfigNumberEntities:
    """
    Tests for host configuration number entities.
    """
    # pylint: disable=too-many-positional-arguments,too-many-arguments
    async def test_host_config_number_entities(
        self,
        unique_id: str, field: str, value: int,
        hass: HomeAssistant, mock_g90alarm: AlarmMockT
    ) -> None:
        """
        Tests host config number entities can be set correctly.
        """
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={'ip_addr': 'dummy-ip'},
            options={},
            entry_id="test_host_config_number"
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        entity_id = hass_get_entity_id_by_unique_id(hass, 'number', unique_id)

        # Verify entity exists and has correct min/max
        state = hass.states.get(entity_id)
        assert state is not None

        # Set the value
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
            blocking=True,
        )
        await hass.async_block_till_done()

        # Verify save was called
        (await mock_g90alarm.return_value.host_config()).save.assert_called()
        # Verify the value was set correctly
        assert getattr(
            await mock_g90alarm.return_value.host_config(), field
        ) == value

    # pylint: disable=too-many-positional-arguments,too-many-arguments
    async def test_host_config_number_data_change(
        self,
        unique_id: str, field: str, value: int,
        hass: HomeAssistant, mock_g90alarm: AlarmMockT
    ) -> None:
        """
        Tests data change propagation in host config number entities.
        """
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={'ip_addr': 'dummy-ip'},
            options={},
            entry_id="test_host_config_number_data_change"
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        # Simulate data update
        setattr(await mock_g90alarm.return_value.host_config(), field, value)

        # Simulate some time has passed for HomeAssistant to invoke
        # update for coordinators and entities
        async_fire_time_changed(hass, dt.utcnow() + timedelta(hours=1))
        await hass.async_block_till_done()

        # Verify the entity state was updated correctly
        entity_id = hass_get_entity_id_by_unique_id(hass, 'number', unique_id)
        entity = hass.states.get(entity_id)
        assert entity is not None
        assert entity.state == str(float(value))


async def test_host_config_number_exception(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests host config number entities handle exceptions correctly.
    """
    (
        await mock_g90alarm.return_value.host_config()
    ).save.side_effect = G90Error('dummy exception')

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_host_config_number_exception"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'number', 'dummy_guid_alarm_siren_duration'
    )

    # Attempt to set value, which should not raise an exception
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: 120},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify save was called despite exception
    (await mock_g90alarm.return_value.host_config()).save.assert_called()
