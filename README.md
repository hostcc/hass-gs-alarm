[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Latest release](https://img.shields.io/github/v/release/hostcc/hass-g90)](https://github.com/hostcc/hass-g90/releases/latest)

# Custom Home Assistant integration for G90 security systems

## Description

The integration supports G90-based security systems might be distributed under
different vendors - Golden Security, Kerui etc. Those having G90 in the model
name has a good chance to be supported - please give it a try and report back.

Actual interface with the security system is implemented via
[pyg90alarm](https://pypi.org/project/pyg90alarm/) Python package.
Please see [its documentation](https://pyg90alarm.readthedocs.io/) for more
details, especially on enabling the device notifications.

Basically, for HomeAssistant to receive notifications from the device on its
state changes and sensor activity the device should have its IP address set to
`10.10.10.250`. That is a specific limitation of how device's firmware works.

## Installation

* Install HACS by following [Setup](https://hacs.xyz/docs/setup/prerequisites)
  and [Configuration](https://hacs.xyz/docs/configuration/basic) steps
* Add `https://github.com/hostcc/hass-g90/` as custom repository of
  `Integration` type, as per [Custom
  repositories](https://hacs.xyz/docs/faq/custom_repositories) instructions for
  HACS
* Add the `g90` integration in HomeAssistant


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
    homeassistant.g90: debug
    custom_components.g90: debug
```
