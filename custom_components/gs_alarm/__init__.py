"""The gs_alarm integration."""
from __future__ import annotations

from pyg90alarm import G90Alarm
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["alarm_control_panel", "switch", "binary_sensor"]

async def options_update_listener(hass, entry):
    """ Handle options update. """
    g90_client = hass.data[DOMAIN][entry.entry_id]['client']
    g90_client.sms_alert_when_armed = entry.options.get(
        'sms_alert_when_armed', False
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up gs_alarm from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    g90_client = G90Alarm(host=entry.data.get('ip_addr', None))
    host_info = await g90_client.host_info
    hass.data[DOMAIN][entry.entry_id] = {
        'client': g90_client,
        'guid': host_info.host_guid,
        'device': {
            'name': f'{DOMAIN}:{host_info.host_guid}',
            'model': host_info.product_name,
            'sw_version': f'MCU: {host_info.mcu_hw_version},'
                          f' WiFi: {host_info.wifi_hw_version}',
            'identifiers': {
                (DOMAIN, host_info.host_guid)
            },
            'manufacturer': 'Golden Security',
        }
    }
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    await g90_client.listen_device_notifications()

    entry.async_on_unload(entry.add_update_listener(options_update_listener))
    # Force setting options upon entry added
    await options_update_listener(hass, entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN][entry.entry_id]['client'].close_device_notifications()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
