[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![Latest release](https://img.shields.io/github/v/release/hostcc/hass-gs-alarm)](https://github.com/hostcc/hass-gs-alarm/releases/latest)

# Custom Home Assistant integration for G90 security systems

## Description

The integration supports G90-based security systems might be distributed under
different vendors - Golden Security, PST, Kerui etc. Those having G90 in the
model name has a good chance to be supported - please give it a try and report
back.

Actual interface with the security system is implemented via
[pyg90alarm](https://pypi.org/project/pyg90alarm/) Python package.
Please see [its documentation](https://pyg90alarm.readthedocs.io/) for more
details, especially on enabling the device notifications.

Basically, for HomeAssistant to receive notifications from the device on its
state changes and sensor activity the device should have its IP address set to
`10.10.10.250`. That is a specific limitation of how device's firmware works.

**NOTE** If you're unable to move your alarm panel to the address above, the
integration will have additional limitations:
* Delays reflecting panel status up to 30 seconds
* Sensor state changes will be absent

Additionally, you might want to enable door close alerts ("Alarm Alert -> Door
close" in mobile application), so the integration properly reflects the state
of a door sensor.  Not enabling it will lead the sensor to become inactive in 3
seconds, same behavior as for other sensors types. This is another limitation
of the device, as it doesn't indicate when the sensor became inactive for most
of the cases.
Please note enabling the door alert will have more notifications (and possible
SMS messages if you enabled those in mobile application) to be sent.


## Installation

* Install HACS by following [Setup](https://hacs.xyz/docs/setup/prerequisites)
  and [Configuration](https://hacs.xyz/docs/configuration/basic) steps
* Download `Golden Security Alarm` integration in HACS
* Add the `Golden Security Alarm` integration in HomeAssistant

## Specifics

* The integration doesn't manage most of settings for the alarm panel, including
  adding/removing sensors - you can only enable/disable sensors/realy. For the
  rest you will still need the mobile application
* No cloud or Internet connectivity required in case of local setup (Home
  Assistant in the same local network as the alarm panel)
* Changes in alarm panel with regards to sensors and switches require the
  integration to be reloaded, it currently does not support making those
  updates available in HomeAssistant without the restart
* If your alarm panel is in a subnet different from one HomeAssistant runs,
  making the intergration receiving the device notification messages will
  require additional steps - the notifications are sent by alarm panel as
  broadcast packets, thus you'll need those forwarded to the HomeAssistant
  subnet


## Troubleshooting

If you need to troubleshoot the integration it is recommended to first enable
debug logging for it, to capture additional details.

For that you'll need to add following options to HomeAssistant's
`configuration.yaml`. Please note this will also set logging level to `info`
for all other HomeAssistant components - please adjust `default: info` to fit
your needs.

```
logger:
  default: info
  logs:
    pyg90alarm: debug
    homeassistant.gs_alarm: debug
    custom_components.gs_alarm: debug
```
