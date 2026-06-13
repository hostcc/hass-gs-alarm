# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Tests for text entities in the custom component.
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

from homeassistant.components.text.const import (
    ATTR_VALUE,
    DOMAIN as TEXT_DOMAIN,
    SERVICE_SET_VALUE,
)

from pyg90alarm import G90Error

from custom_components.gs_alarm.const import DOMAIN
from .conftest import (
    AlarmMockT,
    hass_get_entity_id_by_unique_id,
    entry_ids_for_integration_devices,
    allow_callbacks_to_complete,
)


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
    await allow_callbacks_to_complete(hass)

    entity_id = hass_get_entity_id_by_unique_id(hass, 'text', unique_id)

    # Set the value
    await hass.services.async_call(
        TEXT_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
        blocking=True,
    )
    await allow_callbacks_to_complete(hass)

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
class TestAlarmPhonesTextEntities:
    """
    Tests for alarm phones text entities.
    """
    # pylint: disable=too-many-positional-arguments,too-many-arguments
    async def test_alarm_phones_text_entities(
        self,
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
        await allow_callbacks_to_complete(hass)

        entity_id = hass_get_entity_id_by_unique_id(hass, 'text', unique_id)

        # Set the value
        await hass.services.async_call(
            TEXT_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
            blocking=True,
        )
        await allow_callbacks_to_complete(hass)

        # Verify save was called
        (await mock_g90alarm.return_value.alarm_phones()).save.assert_called()
        # Verify the value was set correctly
        assert getattr(
            await mock_g90alarm.return_value.alarm_phones(), field
        ) == value

    # pylint: disable=too-many-positional-arguments,too-many-arguments
    async def test_alarm_phones_text_data_change(
        self,
        unique_id: str, field: str, value: str,
        hass: HomeAssistant, mock_g90alarm: AlarmMockT
    ) -> None:
        """
        Tests data change propagation in alarm phones text entities.
        """
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={'ip_addr': 'dummy-ip'},
            options={},
            entry_id="test_alarm_phones_text_data_change"
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await allow_callbacks_to_complete(hass)

        # Simulate data update
        setattr(await mock_g90alarm.return_value.alarm_phones(), field, value)

        # Simulate some time has passed for HomeAssistant to invoke
        # update for coordinators and entities
        async_fire_time_changed(hass, dt.utcnow() + timedelta(hours=1))
        await allow_callbacks_to_complete(hass)

        # Verify the entity state was updated correctly
        entity_id = hass_get_entity_id_by_unique_id(hass, 'text', unique_id)
        entity = hass.states.get(entity_id)
        assert entity is not None
        assert entity.state == value


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
    await allow_callbacks_to_complete(hass)

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
    await allow_callbacks_to_complete(hass)

    # Verify save was called despite exception
    (await mock_g90alarm.return_value.alarm_phones()).save.assert_called()


@pytest.mark.parametrize("unique_id,field,value", [
    pytest.param(
        "dummy_guid_sia_host", "host", "192.168.1.1",
        id="SIA host"
    ),
    pytest.param(
        "dummy_guid_sia_account", "account", "test_account",
        id="SIA account"
    ),
    pytest.param(
        "dummy_guid_sia_receiver", "receiver", "1234567890",
        id="SIA receiver"
    ),
    pytest.param(
        "dummy_guid_sia_prefix", "prefix", "test_prefix",
        id="SIA prefix"
    ),
    pytest.param(
        "dummy_guid_sia_aes_key", "aes_key", "1234567890",
        id="SIA AES key"
    ),
])
async def test_sia_config_text_entities(
    unique_id: str, field: str, value: str,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests SIA config text entities can be set correctly.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_sia_config_text_entities"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    entity_id = hass_get_entity_id_by_unique_id(hass, 'text', unique_id)
    # Set the value
    await hass.services.async_call(
        TEXT_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
        blocking=True,
    )
    await allow_callbacks_to_complete(hass)

    # Verify save was called
    (await mock_g90alarm.return_value.sia_config()).save.assert_called()
    # Verify the value was set correctly
    assert getattr(
        await mock_g90alarm.return_value.sia_config(), field
    ) == value


@pytest.mark.parametrize("unique_id,field,value", [
    pytest.param(
        "dummy_guid_cid_phone1", "phone1", "1234567890",
        id="CID phone 1"
    ),
    pytest.param(
        "dummy_guid_cid_phone2", "phone2", "1234567890",
        id="CID phone 2"
    ),
    pytest.param(
        "dummy_guid_cid_user", "user", "t_user",
        id="CID user"
    ),
])
async def test_cid_config_text_entities(
    unique_id: str, field: str, value: str,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Tests CID config text entities can be set correctly.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_cid_config_text_entities"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    entity_id = hass_get_entity_id_by_unique_id(hass, 'text', unique_id)
    # Set the value
    await hass.services.async_call(
        TEXT_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
        blocking=True,
    )
    await allow_callbacks_to_complete(hass)

    # Verify save was called
    (await mock_g90alarm.return_value.cid_config()).save.assert_called()
    # Verify the value was set correctly
    assert getattr(
        await mock_g90alarm.return_value.cid_config(), field
    ) == value


@pytest.mark.parametrize(
    "unique_id,old_name,new_name,all_entities_call,"
    "expect_name_change,simulated_exception",
    [
        pytest.param(
            "dummy_guid_sensor_0_panel_name",
            "Dummy sensor", "Renamed sensor",
            "get_sensors",
            True, None,
            id="Rename sensor"
        ),
        pytest.param(
            "dummy_guid_switch_0_panel_name",
            "Dummy switch 1", "Renamed relay",
            "get_devices",
            True, None,
            id="Rename device"
        ),
        pytest.param(
            "dummy_guid_sensor_0_panel_name",
            "Dummy sensor", "  ",
            "get_sensors",
            False, None,
            id="Empty sensor name"
        ),
        pytest.param(
            "dummy_guid_switch_0_panel_name",
            "Dummy switch 1", "  ",
            "get_devices",
            False, None,
            id="Empty device name"
        ),
        pytest.param(
            "dummy_guid_sensor_0_panel_name",
            "Dummy sensor", "Dummy sensor",
            "get_sensors",
            False, G90Error('dummy exception'),
            id="Exception when renaming sensor"
        ),
        pytest.param(
            "dummy_guid_switch_0_panel_name",
            "Dummy switch 1", "Dummy switch 1",
            "get_devices",
            False, G90Error('dummy exception'),
            id="Exception when renaming device"
        ),
    ],
)
async def test_rename_text_entities(
    unique_id: str, old_name: str, new_name: str,
    all_entities_call: str, expect_name_change: bool,
    simulated_exception: G90Error,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    """
    Tests text entities for renaming sensors and devices.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_rename_text_entities"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await allow_callbacks_to_complete(hass)

    # Find the alarm entity (sensor or device) to rename
    alarm_entity = next(
        iter(
            x for x in await getattr(mock_g90alarm, all_entities_call)()
            if x.name == old_name
        )
    )
    # Simulate an exception when renaming the entity if requested
    alarm_entity.set_name.side_effect = simulated_exception

    # Attempt to rename the entity
    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'text', unique_id
    )
    await hass.services.async_call(
        TEXT_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: new_name},
        blocking=True,
    )
    await allow_callbacks_to_complete(hass)

    # Verify the entity name has been changed if requested
    new_entity_name = new_name if expect_name_change else old_name
    assert any(
        x['device'] == new_entity_name
        for x in entry_ids_for_integration_devices(
            hass, config_entry.entry_id
        )
    )

    if not expect_name_change and not simulated_exception:
        # Verify the corresponding call has not been made
        alarm_entity.set_name.assert_not_called()
    else:
        # Verify the corresponding call has been made (either successfully
        # or with an exception)
        alarm_entity.set_name.assert_called_once_with(new_name)
