"""
tbd
"""
from datetime import timedelta
from unittest.mock import patch, AsyncMock

from pytest_unordered import unordered

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from homeassistant.util import dt
import homeassistant.helpers.device_registry as dr
import homeassistant.helpers.entity_registry as er

import pyg90alarm

from custom_components.gs_alarm import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.gs_alarm.const import DOMAIN


async def test_setup_unload_and_reload_entry(hass):
    """
    tbd
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={'ip_addr': 'dummy-ip'},
        options={'disabled_sensors': ['Dummy sensor#1']},
        entry_id="test"
    )
    config_entry.add_to_hass(hass)
    with patch('custom_components.gs_alarm.G90Alarm', autospec=True) as mock:
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

        mock.return_value.get_sensors = AsyncMock(
            return_value=[
                pyg90alarm.alarm.G90Sensor(
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
        assert await async_setup_entry(hass, config_entry)
        async_fire_time_changed(hass, dt.utcnow() + timedelta(hours=1))
        await hass.async_block_till_done()

        mock.assert_called_once_with(host='dummy-ip')

        integration_devices = dr.async_entries_for_config_entry(
            dr.async_get(hass), config_entry.entry_id
        )
        assert len(integration_devices) == 1
        integration_device_id = integration_devices[0].id

        integration_entities = er.async_entries_for_device(
            er.async_get(hass), integration_device_id
        )
        integration_entity_ids = [x.entity_id for x in integration_entities]
        assert integration_entity_ids == unordered([
            'alarm_control_panel.dummy',
            'binary_sensor.dummy_sensor_1',
            'switch.dummy_switch_1',
            'sensor.gs_alarm_wifi_signal',
            'binary_sensor.gs_alarm_wifi_status',
            'sensor.gs_alarm_gsm_signal',
            'binary_sensor.gs_alarm_gsm_status'
        ])

        assert await async_unload_entry(hass, config_entry)
