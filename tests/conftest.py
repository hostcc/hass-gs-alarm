"""
tbd
"""
from unittest.mock import patch, AsyncMock, PropertyMock
import pytest

import pyg90alarm


@pytest.fixture(autouse=True)
# pylint: disable=unused-argument
def auto_enable_custom_integrations(enable_custom_integrations):
    """
    tbd
    """
    yield


def pytest_configure(config):
    """
    tbd
    """
    config.addinivalue_line("markers", "g90discovery")


@pytest.fixture
def mock_g90alarm(request):
    """
    tbd
    """
    with (
        patch('custom_components.gs_alarm.G90Alarm', autospec=True) as mock,
        patch(
            'custom_components.gs_alarm.config_flow.G90Alarm.discover'
        ) as mock_discover,
    ):
        mock_discover.return_value = (
            getattr(
                request.node
                .get_closest_marker('g90discovery'),
                'kwargs', {}
            ).get('result', [])
        )

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

        mock.return_value.get_host_status = AsyncMock(
            return_value=pyg90alarm.alarm.G90HostStatus(
                host_status=pyg90alarm.alarm.G90ArmDisarmTypes.DISARM,
                host_phone_number=None,
                product_name='Dummy product',
                mcu_hw_version='1.0',
                wifi_hw_version='1.0',
            )
        )

        mock_sensor = pyg90alarm.alarm.G90Sensor(
            parent=mock.return_value, subindex=0, proto_idx=0,
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
        mock_sensor.set_enabled = AsyncMock()
        type(mock_sensor).supports_enable_disable = (
            PropertyMock(return_value=True)
        )

        mock.return_value.get_sensors = AsyncMock(
            return_value=[
                mock_sensor,
            ]
        )

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

        mock.return_value.listen_device_notifications = AsyncMock()

        yield mock
