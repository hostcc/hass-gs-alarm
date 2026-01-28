# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Ilia Sotnikov
"""
Data update coordinator for the `gs-alarm` integration.
"""
from __future__ import annotations
from typing import List, TYPE_CHECKING, Optional, Callable
import logging
from dataclasses import dataclass
from datetime import datetime

from pyg90alarm import (
    G90Alarm, G90Error, G90TimeoutError,
    G90Sensor, G90Device, G90HostInfo, G90HostStatus,
    G90AlertConfigFlags, G90HostConfig, G90NetConfig, G90AlarmPhones,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed
)
from .const import DOMAIN, SCAN_INTERVAL
if TYPE_CHECKING:
    from . import GsAlarmConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass
class GsAlarmData:
    """
    Class to hold alarm panel data.
    """
    # pylint: disable=too-many-instance-attributes
    sensors: List[G90Sensor]
    devices: List[G90Device]
    host_info: G90HostInfo
    host_status: G90HostStatus
    alert_config_flags: G90AlertConfigFlags
    host_config: G90HostConfig
    net_config: G90NetConfig
    alarm_phones: G90AlarmPhones
    last_device_packet_time: Optional[datetime]
    last_upstream_packet_time: Optional[datetime]

    @property
    def get_alarm_phones_func(self) -> Callable[[], G90AlarmPhones]:
        """
        Get a callable that returns the alarm phones data.

        Callable is needed to ensure the latest object is used, since
        `G90Alarm.get_alarm_phones()` method returns a new instance every time.

        :return: Callable returning G90AlarmPhones
        """
        def wrapper() -> G90AlarmPhones:
            return self.alarm_phones
        return wrapper

    @property
    def get_host_config_func(self) -> Callable[[], G90HostConfig]:
        """
        Get a callable that returns the host config data.

        Callable is needed to ensure the latest object is used, since
        `G90Alarm.get_host_config()` method returns a new instance every time.

        :return: Callable returning G90HostConfig
        """
        def wrapper() -> G90HostConfig:
            return self.host_config
        return wrapper

    @property
    def get_net_config_func(self) -> Callable[[], G90NetConfig]:
        """
        Get a callable that returns the network config data.

        Callable is needed to ensure the latest object is used, since
        `G90Alarm.get_net_config()` method returns a new instance every time.

        :return: Callable returning G90NetConfig
        """
        def wrapper() -> G90NetConfig:
            return self.net_config
        return wrapper


class GsAlarmCoordinator(DataUpdateCoordinator[GsAlarmData]):
    """
    Data update coordinator.

    :param hass: Home Assistant instance
    :param entry: Configuration entry for the G90 Alarm integration
    :param g90_client: Instance of the G90Alarm client
    """
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self, hass: HomeAssistant, entry: GsAlarmConfigEntry,
        g90_client: G90Alarm
    ) -> None:
        # No `setup()` method is used currently as it is called too late,
        # `init_essential_data` is used instead (see below)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            config_entry=entry,
            update_method=self.update,
            update_interval=SCAN_INTERVAL,
        )
        self.client = g90_client

    async def init_essential_data(self) -> None:
        """
        Initialize the coordinator by fetching the essential data.

        The main purpose of this method is to fetch the essential data to
        support creating entities depend on this data. As an example, the GUID
        is used in most of unique IDs - the `update()` method will also trigger
        callbacks for sensor and device lists, in turn resulting in entity
        creation but the GUID might be fetched later than that due to
        asynchronous nature of the callbacks and `pyg90alarm` library.

        This logic would fit the constructor, however invoking async methods
        there will lead to complications, hence a separate method is used.
        """
        _LOGGER.info("Initializing coordinator with essential data")
        host_info = await self.client.get_host_info()
        host_status = await self.client.get_host_status()
        host_config = await self.client.host_config()
        net_config = await self.client.net_config()
        alarm_phones = await self.client.alarm_phones()
        self.async_set_updated_data(
            GsAlarmData(
                sensors=[],
                devices=[],
                host_info=host_info,
                host_status=host_status,
                alert_config_flags=G90AlertConfigFlags(0),
                host_config=host_config,
                net_config=net_config,
                alarm_phones=alarm_phones,
                last_device_packet_time=None,
                last_upstream_packet_time=None,
            )
        )
        _LOGGER.debug("Coordinator data: %s", self.data)

    async def update(self) -> GsAlarmData:
        """
        Update the coordinator data.
        """
        _LOGGER.debug("Updating coordinator")
        try:
            data = GsAlarmData(
                sensors=await self.client.get_sensors(),
                devices=await self.client.get_devices(),
                host_info=await self.client.get_host_info(),
                host_status=await self.client.get_host_status(),
                alert_config_flags=await self.client.get_alert_config(),
                host_config=await self.client.host_config(),
                net_config=await self.client.net_config(),
                alarm_phones=await self.client.alarm_phones(),
                last_device_packet_time=self.client.last_device_packet_time,
                last_upstream_packet_time=(
                    self.client.last_upstream_packet_time
                ),
            )
            _LOGGER.debug("Coordinator data: %s", data)
            return data
        except G90TimeoutError as exc:
            raise UpdateFailed(
                f"Timeout updating panel '{self.data.host_info.host_guid}'"
            ) from exc
        except G90Error as exc:
            raise UpdateFailed(f"Error: {repr(exc)}") from exc
