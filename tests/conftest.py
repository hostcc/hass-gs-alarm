# SPDX-License-Identifier: MIT
# Copyright (c) 2022 Ilia Sotnikov
"""
Pytest configuration and fixtures
"""
from __future__ import annotations
from typing import Iterator, TypeVar, Any, AsyncGenerator, Dict, List
from unittest.mock import patch, AsyncMock, PropertyMock
import pytest

from homeassistant.core import HomeAssistant, State
import homeassistant.helpers.entity_registry as er
import homeassistant.helpers.device_registry as dr

from pyg90alarm import (
    G90Alarm,
    G90ArmDisarmTypes,
    G90AlertConfigFlags,
    G90HostInfo,
    G90HostStatus,
    G90Sensor,
    G90SensorUserFlags,
    G90Device,
    G90History,
    G90NetConfig,
    G90AlarmPhones,
    G90HostConfig,
)

AlarmMockT = TypeVar('AlarmMockT', bound=AsyncMock)


@pytest.fixture(autouse=True)
# pylint: disable=unused-argument
def auto_enable_custom_integrations(
    enable_custom_integrations: pytest.FixtureDef[HomeAssistant]
) -> Iterator[None]:
    """
    Automatically uses `enable_custom_integrations` Homeassistant fixture,
    since it is required for custom integrations to be loaded during tests.
    """
    yield None


def pytest_configure(config: pytest.Config) -> None:
    """
    Configures `pytest`.
    """
    # Register `g90discovery` mark allows to specify mocked G90 discovery
    # results
    config.addinivalue_line("markers", "g90discovery")

    # Register `g90host_status` mark allows to specify status of mocked G90
    # panel
    config.addinivalue_line("markers", "g90host_status")


@pytest.fixture
def mock_g90alarm(request: pytest.FixtureRequest) -> Iterator[AlarmMockT]:
    """
    Mocks `G90Alarm` instance and its methods relevant to tests.
    Methods not explicitly mocked will be passed through to the real
    implementation.
    """
    # Mock results for discovery from mark or default to empty list
    discovery_results = getattr(
        request.node.get_closest_marker('g90discovery'),
        'kwargs', {}
    ).get('result', [])

    # Mocked panel status from mark or default to disarmed
    host_status = getattr(
        request.node.get_closest_marker('g90host_status'),
        'kwargs', {}
    ).get('result', G90ArmDisarmTypes.DISARM)

    # Create host info return value
    host_info = G90HostInfo(
        host_guid='Dummy GUID',
        product_name='Dummy product',
        wifi_protocol_version='1.0-test',
        cloud_protocol_version='1.1-test',
        mcu_hw_version='1.0-test',
        wifi_hw_version='1.0-test',
        gsm_status_data=0,
        wifi_status_data=0,
        gprs_3g_active_data=1,
        wifi_setup_progress_data=0,
        battery_voltage='4567',
        gsm_signal_level=100,
        wifi_signal_level=100,
    )

    async def sensor_list_fetch(
        *_args: Any, **_kwargs: Any
    ) -> AsyncGenerator[G90Sensor, None]:
        """
        Mocked sensor list fetch method.
        """
        mock_sensors = [
            G90Sensor(
                # Has to point to `G90Alarm()` instance
                parent=mock.return_value,
                subindex=0, proto_idx=0,
                parent_name='Dummy sensor',
                index=0,
                room_id=0,
                type_id=1,
                subtype=1,
                timeout=0,
                user_flags_data=(
                    G90SensorUserFlags.ENABLED
                    | G90SensorUserFlags.ALERT_WHEN_AWAY
                    | G90SensorUserFlags.SUPPORTS_UPDATING_SUBTYPE
                ),
                baudrate=0,
                protocol_id=0,
                reserved_data=0,
                node_count=1,
                mask=0,
                private_data=0,
            )
        ]
        for mock_sensor in mock_sensors:
            mock_sensor.set_alert_mode = (  # type: ignore[method-assign]
                AsyncMock()
            )
            mock_sensor.set_flag = AsyncMock()  # type: ignore[method-assign]
            mock_sensor.delete = AsyncMock()  # type: ignore[method-assign]

            yield mock_sensor

    async def device_list_fetch(
        *_args: Any, **_kwargs: Any
    ) -> AsyncGenerator[G90Device, None]:
        """
        Mocked device list fetch method.
        """
        mock_devices = [
            G90Device(
                parent=mock.return_value, subindex=0, proto_idx=1,
                parent_name='Dummy switch 1',
                index=0,
                room_id=0,
                type_id=128,
                subtype=0,
                timeout=0,
                user_flags_data=0,
                baudrate=0,
                protocol_id=0,
                reserved_data=0,
                node_count=1,
                mask=0,
                private_data=0,
            ),
            G90Device(
                parent=mock.return_value, subindex=0, proto_idx=2,
                parent_name='Dummy switch 2 multi-node',
                index=1,
                room_id=0,
                type_id=128,
                subtype=0,
                timeout=0,
                user_flags_data=0,
                baudrate=0,
                protocol_id=0,
                reserved_data=0,
                node_count=2,
                mask=0,
                private_data=0,
            ),
            G90Device(
                parent=mock.return_value, subindex=1, proto_idx=2,
                parent_name='Dummy switch 2 multi-node',
                index=1,
                room_id=0,
                type_id=128,
                subtype=0,
                timeout=0,
                user_flags_data=0,
                baudrate=0,
                protocol_id=0,
                reserved_data=0,
                node_count=2,
                mask=0,
                private_data=0,
            ),
            G90Device(
                parent=mock.return_value, subindex=0, proto_idx=3,
                parent_name='Dummy switch 3 multi-node',
                index=2,
                room_id=0,
                type_id=128,
                subtype=0,
                timeout=0,
                user_flags_data=0,
                baudrate=0,
                protocol_id=0,
                reserved_data=0,
                node_count=2,
                mask=0,
                private_data=0,
            ),
            G90Device(
                parent=mock.return_value, subindex=1, proto_idx=3,
                parent_name='Dummy switch 3 multi-node',
                index=2,
                room_id=0,
                type_id=128,
                subtype=0,
                timeout=0,
                user_flags_data=0,
                baudrate=0,
                protocol_id=0,
                reserved_data=0,
                node_count=2,
                mask=0,
                private_data=0,
            )
        ]

        for mock_device in mock_devices:
            mock_device.turn_on = AsyncMock()  # type: ignore[method-assign]
            mock_device.turn_off = AsyncMock()  # type: ignore[method-assign]
            mock_device.delete = AsyncMock()  # type: ignore[method-assign]

            yield mock_device

    with (
        # Mock the discover class method for config flow
        patch(
            'custom_components.gs_alarm.config_flow.G90Alarm.discover',
            return_value=discovery_results
        ),
        # Main G90Alarm mock with wrapping of the real implementation
        patch(
            'custom_components.gs_alarm.G90Alarm',
            spec=G90Alarm,
            # Create a real instance to wrap
            wraps=G90Alarm('dummy-mocked-host')
        ) as mock,
        patch(
            'pyg90alarm.entities.sensor_list.G90SensorList._fetch',
            autospec=True,
            side_effect=sensor_list_fetch
        ),
        patch(
            'pyg90alarm.entities.device_list.G90DeviceList._fetch',
            autospec=True,
            side_effect=device_list_fetch
        ),
        patch(
            'pyg90alarm.local.config.G90AlertConfig.flags',
            new_callable=PropertyMock,
            side_effect=AsyncMock(
                return_value=G90AlertConfigFlags(~0)
            ),
        ),
        patch(
            'pyg90alarm.local.config.G90AlertConfig.flags_with_fallback',
            new_callable=PropertyMock,
            side_effect=AsyncMock(
                return_value=G90AlertConfigFlags(~0)
            ),
        ),
        patch(
            'pyg90alarm.local.config.G90AlertConfig.set_flag',
            autospec=True,
        ),

        # Patching dataclass `save()` method should come before `load()`,
        # since load returns instance of the dataclass. Otherwise, `save()`
        # won't get mocked correctly. Also, `autospec=True` isn't used,
        # otherwise mock instance won't get created over `save()` method.
        patch(
            'pyg90alarm.local.host_config.G90HostConfig.save',
        ),
        patch(
            'pyg90alarm.local.host_config.G90HostConfig.load',
            autospec=True,
            side_effect=AsyncMock(
                return_value=G90HostConfig(
                    _speech_language=1,
                    _alarm_volume_level=2,
                    alarm_siren_duration=120,
                    arm_delay=30,
                    alarm_delay=45,
                    backlight_duration=60,
                    ring_duration=10,
                    timezone_offset_m=-300,
                    _speech_volume_level=2,
                    _key_tone_volume_level=0,
                    _ring_volume_level=2,
                )
            )
        ),
        # See comment above about patching order
        patch(
            'pyg90alarm.local.net_config.G90NetConfig.save',
        ),
        patch(
            'pyg90alarm.local.net_config.G90NetConfig.load',
            autospec=True,
            side_effect=AsyncMock(
                return_value=G90NetConfig(
                    _ap_enabled=0,
                    ap_password='123456789',
                    _wifi_enabled=1,
                    _gprs_enabled=1,
                    _apn_auth=2,
                    apn_user='apn_user',
                    apn_password='aps_pass',
                    apn_name='an_apn',
                    gsm_operator='12345',
                )
            ),
        ),
        # See comment above about patching order
        patch(
            'pyg90alarm.local.alarm_phones.G90AlarmPhones.save',
        ),
        patch(
            'pyg90alarm.local.alarm_phones.G90AlarmPhones.load',
            autospec=True,
            side_effect=AsyncMock(
                return_value=G90AlarmPhones(
                    panel_password='1234',
                    panel_phone_number='8877665544',
                    phone_number_1='', phone_number_2='', phone_number_3='',
                    phone_number_4='', phone_number_5='', phone_number_6='',
                    sms_push_number_1='00987654321', sms_push_number_2='',
                )
            ),
        ),
        patch(
            'pyg90alarm.G90Alarm.history',
            autospec=True,
            return_value=[
                # Valid entry
                G90History(
                    type=2,
                    event_id=3,
                    source=0,
                    state=0,
                    sensor_name='',
                    unix_time=3,
                    other=''
                ),
                # Invalid entry (wrong source)
                G90History(
                    type=2,
                    event_id=3,
                    source=254,
                    state=0,
                    sensor_name='',
                    unix_time=3,
                    other=''
                )
            ]
        ),
        patch(
            'pyg90alarm.G90Alarm.get_host_info',
            autospec=True,
            return_value=host_info
        ),
        patch(
            'pyg90alarm.G90Alarm.get_host_status',
            autospec=True,
            return_value=G90HostStatus(
                host_status_data=host_status,
                host_phone_number='12345678',
                product_name='Dummy product',
                mcu_hw_version='1.0-test',
                wifi_hw_version='1.0-test',
            )
        ),
        patch(
            'pyg90alarm.G90Alarm.listen_notifications',
            autospec=True
        ),
        patch(
            'pyg90alarm.G90Alarm.register_sensor',
            autospec=True,
            return_value=G90Sensor(
                # Has to point to `G90Alarm()` instance
                parent=mock.return_value,
                subindex=0, proto_idx=99,
                parent_name='Registered sensor',
                index=99,
                room_id=0,
                type_id=1,
                subtype=1,
                timeout=0,
                user_flags_data=0,
                baudrate=0,
                protocol_id=0,
                reserved_data=0,
                node_count=1,
                mask=0,
                private_data=0,
            )
        ),
        patch(
            'pyg90alarm.G90Alarm.register_device',
            autospec=True,
            return_value=G90Device(
                parent=mock.return_value, subindex=0, proto_idx=99,
                parent_name='Registered device',
                index=99,
                room_id=0,
                type_id=128,
                subtype=0,
                timeout=0,
                user_flags_data=0,
                baudrate=0,
                protocol_id=0,
                reserved_data=0,
                node_count=1,
                mask=0,
                private_data=0,
            )
        ),
        patch(
            'pyg90alarm.G90Alarm.set_cloud_server_address',
            autospec=True,
        ),
    ):
        yield mock


def hass_get_entity_id_by_unique_id(
    hass: HomeAssistant,
    platform: str,
    unique_id: str,
) -> str:
    """
    Returns entity ID for given unique ID.
    """
    entity_registry = er.async_get(hass)

    entity_id = entity_registry.async_get_entity_id(
        platform, 'gs_alarm', unique_id
    )
    assert entity_id is not None, (
        f'Entity with unique ID {unique_id} not found in {platform} '
        'platform'
    )
    return entity_id


def hass_get_state_by_unique_id(
    hass: HomeAssistant,
    platform: str,
    unique_id: str,
) -> State:
    """
    Returns entity state for given unique ID.
    """
    entity_id = hass_get_entity_id_by_unique_id(hass, platform, unique_id)

    state = hass.states.get(entity_id)
    assert state is not None, (
        f'State for entity with unique ID {unique_id} not found in'
        f' {platform} platform'
    )

    return state


def entry_ids_for_integration_devices(
    hass: HomeAssistant, entry_id: str
) -> List[Dict[str, Any]]:
    """
    Returns a list of entry IDs for all devices integrated with the given
    config entry.
    """
    return [
        {
            'device': x.name,
            'device_id': x.id,
            'entities': [
                {
                    'unique_id': y.unique_id,
                    'entity_id': y.entity_id,
                    'name': y.name or y.original_name
                } for y in er.async_entries_for_device(
                    er.async_get(hass), x.id
                )
            ]
        } for x in dr.async_entries_for_config_entry(
            dr.async_get(hass), entry_id
        )
    ]
