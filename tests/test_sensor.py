# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ilia Sotnikov
"""
Tests sensor entities for the custom component.
"""
from datetime import timedelta

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt

from custom_components.gs_alarm.const import (
    DOMAIN,
    NOTIFICATIONS_PROTOCOL_SENSOR_LAST_DEVICE_TIMESTAMP_ATTR,
    NOTIFICATIONS_PROTOCOL_SENSOR_LAST_UPSTREAM_TIMESTAMP_ATTR,
)
from .conftest import AlarmMockT, hass_get_state_by_unique_id


async def test_notifications_protocol_binary_sensor(
    hass: HomeAssistant, mock_g90alarm: AlarmMockT
) -> None:
    """
    Verify notifications protocol binary sensor startup and TTL behavior.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={'notifications_protocol': 'local'},
        entry_id='test-notifications-protocol',
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify the sensor is initially off, has extra attributes with no
    # timestamps
    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', 'dummy_guid_sensor_notifications_protocol'
    )
    assert sensor_state.state == 'off'
    assert (
        NOTIFICATIONS_PROTOCOL_SENSOR_LAST_DEVICE_TIMESTAMP_ATTR
        in sensor_state.attributes
    )
    assert (
        NOTIFICATIONS_PROTOCOL_SENSOR_LAST_UPSTREAM_TIMESTAMP_ATTR
        in sensor_state.attributes
    )
    assert (
        sensor_state.attributes[
            NOTIFICATIONS_PROTOCOL_SENSOR_LAST_DEVICE_TIMESTAMP_ATTR
        ] is None
    )
    assert (
        sensor_state.attributes[
            NOTIFICATIONS_PROTOCOL_SENSOR_LAST_UPSTREAM_TIMESTAMP_ATTR
        ] is None
    )

    # Simulate a device packet being received, and upstream one been received
    # 10 minutes ago
    last_device_packet_time = dt.utcnow()
    last_upstream_packet_time = dt.utcnow() - timedelta(minutes=10)
    mock_g90alarm.return_value.last_device_packet_time = (
        last_device_packet_time
    )
    mock_g90alarm.return_value.last_upstream_packet_time = (
        last_upstream_packet_time
    )
    # Simulate a time change event, which should trigger the sensor update
    async_fire_time_changed(hass, dt.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()

    # Verify the sensor is now on, with the correct timestamps
    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', 'dummy_guid_sensor_notifications_protocol'
    )
    assert sensor_state.state == 'on'
    assert (
        sensor_state.attributes[
            NOTIFICATIONS_PROTOCOL_SENSOR_LAST_DEVICE_TIMESTAMP_ATTR
        ] == last_device_packet_time
    )
    assert (
        sensor_state.attributes[
            NOTIFICATIONS_PROTOCOL_SENSOR_LAST_UPSTREAM_TIMESTAMP_ATTR
        ] == last_upstream_packet_time
    )

    # Simulate a device packet has been received outside of TTL window
    mock_g90alarm.return_value.last_device_packet_time = (
        dt.utcnow() - timedelta(minutes=3)
    )
    # Keep upstream timestamp fresh to confirm it does not affect state.
    mock_g90alarm.return_value.last_upstream_packet_time = dt.utcnow()
    # Simulate a time change event, which should trigger the sensor update
    async_fire_time_changed(hass, dt.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()

    # Verify the sensor went off
    sensor_state = hass_get_state_by_unique_id(
        hass, 'binary_sensor', 'dummy_guid_sensor_notifications_protocol'
    )
    assert sensor_state.state == 'off'
