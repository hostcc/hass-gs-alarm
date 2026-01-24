# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Tests for text entities in the custom component.
"""
from __future__ import annotations
import pytest

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)

from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_ENTITY_ID

from homeassistant.components.text.const import (
    ATTR_VALUE,
    DOMAIN as TEXT_DOMAIN,
    SERVICE_SET_VALUE,
)

from pyg90alarm import G90Error

from custom_components.gs_alarm.const import DOMAIN
from .conftest import AlarmMockT, hass_get_entity_id_by_unique_id


@pytest.mark.parametrize(
    "unique_id,value,field",
    [
        pytest.param(
            "dummy_guid_ap_password", "test_password123", "ap_password",
            id="AP password"
        ),
        pytest.param(
            "dummy_guid_apn_name", "internet", "apn_name",
            id="APN name"
        ),
        pytest.param(
            "dummy_guid_apn_user", "test_user", "apn_user",
            id="APN user"
        ),
        pytest.param(
            "dummy_guid_apn_password", "apn_pass123", "apn_password",
            id="APN password"
        ),
    ],
)
# pylint: disable=too-many-positional-arguments,too-many-arguments
async def test_net_config_text_entities(
    unique_id: str, value: str, field: str,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests network config text entities can be set correctly.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_net_config_text"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(hass, 'text', unique_id)

    # Set the value
    await hass.services.async_call(
        TEXT_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify save was called
    (await mock_g90alarm.return_value.net_config()).save.assert_called()
    # Verify the value was set correctly
    assert getattr(
        await mock_g90alarm.return_value.net_config(), field
    ) == value


@pytest.mark.parametrize(
    "unique_id,field,value",
    [
        pytest.param(
            "dummy_guid_panel_password", "panel_password",
            "1234",
            id="Panel password"
        ),
        pytest.param(
            "dummy_guid_panel_phone_number", "panel_phone_number",
            "+1234567890",
            id="Panel phone number"
        ),
        pytest.param(
            "dummy_guid_phone_number_1", "phone_number_1",
            "+1111111111",
            id="Alarm phone 1"
        ),
        pytest.param(
            "dummy_guid_phone_number_2", "phone_number_2",
            "+2222222222",
            id="Alarm phone 2"
        ),
        pytest.param(
            "dummy_guid_phone_number_3", "phone_number_3",
            "+3333333333",
            id="Alarm phone 3"
        ),
        pytest.param(
            "dummy_guid_phone_number_4", "phone_number_4",
            "+4444444444",
            id="Alarm phone 4"
        ),
        pytest.param(
            "dummy_guid_phone_number_5", "phone_number_5",
            "+5555555555",
            id="Alarm phone 5"
        ),
        pytest.param(
            "dummy_guid_phone_number_6", "phone_number_6",
            "+6666666666",
            id="Alarm phone 6"
        ),
        pytest.param(
            "dummy_guid_sms_push_number_1", "sms_push_number_1",
            "+7777777777",
            id="SMS push phone 1"
        ),
        pytest.param(
            "dummy_guid_sms_push_number_2", "sms_push_number_2",
            "+8888888888",
            id="SMS push phone 2"
        ),
    ],
)
# pylint: disable=too-many-positional-arguments,too-many-arguments
async def test_alarm_phones_text_entities(
    unique_id: str, field: str, value: str,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests alarm phones text entities can be set correctly.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_alarm_phones_text"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(hass, 'text', unique_id)

    # Set the value
    await hass.services.async_call(
        TEXT_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify save was called
    (await mock_g90alarm.return_value.alarm_phones()).save.assert_called()
    # Verify the value was set correctly
    assert getattr(
        await mock_g90alarm.return_value.alarm_phones(), field
    ) == value


async def test_alarm_phones_text_exception(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests alarm phones text entities handle exceptions correctly.
    """
    (
        await mock_g90alarm.return_value.alarm_phones()
    ).save.side_effect = G90Error('dummy exception')

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_alarm_phones_text_exception"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'text', 'dummy_guid_panel_password'
    )

    # Attempt to set value, which should not raise an exception
    await hass.services.async_call(
        TEXT_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: "test"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify save was called despite exception
    (await mock_g90alarm.return_value.alarm_phones()).save.assert_called()
