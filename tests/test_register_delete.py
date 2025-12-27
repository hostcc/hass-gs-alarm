# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Test cases for registering and deleting sensors/devices in the alarm panel.
"""
from __future__ import annotations
from typing import List
from unittest.mock import ANY
import pytest
from pytest_unordered import unordered

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry, async_capture_events, async_get_persistent_notifications
)

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_ENTITY_ID,
)
from homeassistant.components.button.const import (
    DOMAIN as BUTTON_DOMAIN,
    SERVICE_PRESS
)
from homeassistant.components.select.const import (
    DOMAIN as SELECT_DOMAIN,
    ATTR_OPTION,
    SERVICE_SELECT_OPTION,
)
from homeassistant.components.text.const import (
    DOMAIN as TEXT_DOMAIN,
    ATTR_VALUE,
    SERVICE_SET_VALUE,
)

from custom_components.gs_alarm.const import (
    DOMAIN,
)
from .conftest import (
    hass_get_entity_id_by_unique_id,
    hass_get_state_by_unique_id,
    entry_ids_for_integration_devices,
    AlarmMockT,
)


@pytest.mark.parametrize(
    "unique_id,alarm_entity_name,alarm_all_entities_call,deleted_entities",
    [
        pytest.param(
            'dummy_guid_switch_0_delete', 'Dummy switch 1',
            'get_devices',
            unordered([
                'dummy_guid_switch_0_1',
                'dummy_guid_switch_0_delete',
            ]),
            id='Delete switch'
        ),
        pytest.param(
            'dummy_guid_sensor_0_delete', 'Dummy sensor',
            'get_sensors',
            unordered([
                'dummy_guid_sensor_0',
                'dummy_guid_sensor_0_enabled',
                'dummy_guid_sensor_0_arm_delay',
                'dummy_guid_sensor_0_detect_door',
                'dummy_guid_sensor_0_door_chime',
                'dummy_guid_sensor_0_independent_zone',
                'dummy_guid_sensor_0_alert_mode',
                'dummy_guid_sensor_0_tampered',
                'dummy_guid_sensor_0_low_battery',
                'dummy_guid_sensor_0_open_when_armed',
                'dummy_guid_sensor_0_delete',
            ]),
            id='Delete sensor'
        ),
    ],
)
# pylint: disable=too-many-arguments,too-many-positional-arguments
async def test_delete(
    unique_id: str, alarm_entity_name: str, alarm_all_entities_call: str,
    deleted_entities: List[str],
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Test that pressing the delete button for a device or sensor in the G90
    alarm system triggers the corresponding entity's delete method.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_delete"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'button', unique_id
    )

    # Press the delete button to remove the entity from the panel
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    alarm_entity = next(
        iter(
            x for x in await getattr(mock_g90alarm, alarm_all_entities_call)()
            if x.name == alarm_entity_name
        )
    )
    assert alarm_entity is not None, (
        f"Entity '{alarm_entity_name}' not found"
    )
    alarm_entity.delete.assert_called_once()

    # Verify entities have been removed from HASS
    assert {
        'device': alarm_entity_name,
        'device_id': ANY,
        'entities': deleted_entities
    } not in entry_ids_for_integration_devices(hass, config_entry.entry_id)


@pytest.mark.parametrize(
    "register_unique_id,"
    "new_type_unique_id,new_name_unique_id,new_type,new_name,"
    "expected_call,expected_notification_msg,expected_event",
    [
        pytest.param(
            'dummy_guid_new_device_register',
            'dummy_guid_new_device_type', 'dummy_guid_new_device_name',
            'Socket: S07', 'New device', 'register_device',
            'Registering a new device of type "Socket: S07",'
            ' please ensure it is in learning mode',
            f"{DOMAIN}_new_device_registration",
            id='Register switch'
        ),
        pytest.param(
            'dummy_guid_new_sensor_register',
            'dummy_guid_new_sensor_type', 'dummy_guid_new_sensor_name',
            'Door Sensor: WRDS01', 'New sensor', 'register_sensor',
            'Registering a new sensor of type "Door Sensor: WRDS01",'
            ' please trigger the sensor',
            f"{DOMAIN}_new_sensor_registration",
            id='Register sensor'
        ),
    ]
)
# pylint: disable=too-many-arguments,too-many-positional-arguments
# pylint: disable=too-many-locals
async def test_register(
    register_unique_id: str, new_type_unique_id: str, new_name_unique_id: str,
    new_type: str, new_name: str, expected_call: str,
    expected_notification_msg: str, expected_event: str,
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Test registering a new device or sensor in the G90 alarm system.

    Verifies that the correct registration method is called and that a
    persistent notification with the expected message is generated for the
    user.
    """
    events = async_capture_events(hass, expected_event)
    notifications = async_get_persistent_notifications(hass)

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={},
        entry_id="test_register"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = hass_get_entity_id_by_unique_id(
        hass, 'button', register_unique_id
    )
    type_entity_id = hass_get_entity_id_by_unique_id(
        hass, 'select', new_type_unique_id
    )
    name_entity_id = hass_get_entity_id_by_unique_id(
        hass, 'text', new_name_unique_id
    )

    # Set the new device type to register
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: type_entity_id, ATTR_OPTION: new_type},
        blocking=True,
    )

    # Set the new device name to register
    await hass.services.async_call(
        TEXT_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: name_entity_id, ATTR_VALUE: new_name},
        blocking=True,
    )

    # Register the new device
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    getattr(mock_g90alarm.return_value, expected_call).assert_called_once_with(
        new_type, new_name
    )

    assert any(
        e.data['index'] == 99
        and e.data['registered'] is True
        and e.data['guid'] == 'Dummy GUID'
        and e.event_type == expected_event
        for e in events
    ), f"No matching event {expected_event} found in events: {events}"

    assert any(
        x['message'] == expected_notification_msg
        and x['title'] == 'Dummy GUID'
        for x in notifications.values()
    ), (
        f"No matching notification {expected_notification_msg} found in"
        " notifications: {notifications}"
    )

    # Verify that new device name and type entities have been reset to have no
    # values previously set
    assert hass_get_state_by_unique_id(
        hass, 'select', new_type_unique_id
    ).state == 'unknown'
    assert hass_get_state_by_unique_id(
        hass, 'text', new_name_unique_id
    ).state == ''
