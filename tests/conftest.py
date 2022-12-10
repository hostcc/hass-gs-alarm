"""
Pytest configuration and fixtures
"""
from unittest.mock import patch, AsyncMock, PropertyMock
import pytest

import pyg90alarm


@pytest.fixture(autouse=True)
# pylint: disable=unused-argument
def auto_enable_custom_integrations(enable_custom_integrations):
    """
    Automatically uses `enable_custom_integrations` Homeassistant fixture,
    since it is required for custom integrations to be loaded during tests.
    """
    yield


def pytest_configure(config):
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
def mock_g90alarm(request):
    """
    Mocks `G90Alarm` instance and its methods relevant to tests.
    """
    with (
        # Mock `G90Alarm` instance - it is imported into
        # `custom_components.gs_alarm` namespace using `from pyg90alarm import
        # G90Alarm`
        patch('custom_components.gs_alarm.G90Alarm', autospec=True) as mock,
        # Mock `G90Alarm.discover()` class method being imported into
        # `custom_components.gs_alarm.config_flow` namespace
        patch(
            'custom_components.gs_alarm.config_flow.G90Alarm.discover'
        ) as mock_discover,
    ):
        # Mocked discovery results, either from `g90discovery` mark (`result`
        # keyword) or empty list by default
        mock_discover.return_value = (
            getattr(
                request.node
                .get_closest_marker('g90discovery'),
                'kwargs', {}
            ).get('result', [])
        )

        # Mock `G90Alarm().get_host_info()` method with dummy product
        # information
        mock.return_value.get_host_info = AsyncMock(
            return_value=pyg90alarm.alarm.G90HostInfo(
                host_guid='Dummy',
                product_name='Dummy product',
                wifi_protocol_version='1.0-test',
                cloud_protocol_version='1.1-test',
                mcu_hw_version='1.0-test',
                wifi_hw_version='1.0-test',
                gsm_status_data=0,
                wifi_status_data=0,
                reserved1=None,
                reserved2=None,
                band_frequency=None,
                gsm_signal_level=100,
                wifi_signal_level=100,
            )
        )

        # Mocked panel status, either from `g90host_status` mark (`result`
        # keyword) or disarmed by default
        host_status = getattr(
            request.node
            .get_closest_marker('g90host_status'),
            'kwargs', {}
        ).get('result', pyg90alarm.alarm.G90ArmDisarmTypes.DISARM)

        # Mock `G90Alarm().get_host_info()` method with dummy status
        # information
        mock.return_value.get_host_status = AsyncMock(
            return_value=pyg90alarm.alarm.G90HostStatus(
                host_status=host_status,
                host_phone_number=None,
                product_name='Dummy product',
                mcu_hw_version='1.0-test',
                wifi_hw_version='1.0-test',
            )
        )

        # Instantiate a dummy sensor to mock in `G90Alarm.get_sensors()`
        mock_sensor = pyg90alarm.alarm.G90Sensor(
            parent=mock.return_value,  # Has to point to `G90Alarm()` instance
            subindex=0, proto_idx=0,
            parent_name='Dummy sensor',
            index=0,
            room_id=0,
            type_id=1,
            subtype=0,
            timeout=0,
            user_flag_data=255,
            baudrate=0,
            protocol_id=0,
            reserved_data=0,
            node_count=0,
            mask=0,
            private_data=0,
        )
        # Mock `set_enabled()` method of the sensor, will be used in test
        # assertions
        mock_sensor.set_enabled = AsyncMock()
        # Mock `supports_enable_disable` property of the sensor defaulting to
        # `True`, will later be used by tests to simulate a sensor no
        # supporting enabling/disabling
        type(mock_sensor).supports_enable_disable = (
            PropertyMock(return_value=True)
        )

        # Mock `G90Alarm().get_sensors()` method pretenting to return single
        # sensor above
        mock.return_value.get_sensors = AsyncMock(
            return_value=[
                mock_sensor,
            ]
        )

        # Mock `G90Alarm().get_devices()` method pretenting to return single
        # device (relay)
        mock.return_value.get_devices = AsyncMock(
            return_value=[
                pyg90alarm.alarm.G90Device(
                    parent=mock.return_value, subindex=0, proto_idx=0,
                    parent_name='Dummy switch',
                    index=0,
                    room_id=0,
                    type_id=0,
                    subtype=0,
                    timeout=0,
                    user_flag_data=0,
                    baudrate=0,
                    protocol_id=0,
                    reserved_data=0,
                    node_count=0,
                    mask=0,
                    private_data=0,
                )
            ]
        )

        # Mock `G90Alarm().listen_device_notificaitons()` to do nothing
        mock.return_value.listen_device_notifications = AsyncMock()

        yield mock
