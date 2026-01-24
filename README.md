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

You might want to enable door close alerts ("Alarm Alert -> Door
close" in mobile application), so the integration properly reflects the state
of a door sensor.  Not enabling it will lead the sensor to become inactive in 3
seconds, same behavior as for other sensors types. This is another limitation
of the device, as it doesn't indicate when the sensor became inactive for most
of the cases.
Please note enabling the door alert will have more notifications (and possible
SMS messages if you enabled those in mobile application) to be sent.

## Panel Configuration Options

The panel configuration options are available as Home Assistant entities and can
be configured through the UI - navigate to "Settings -> Devices & Services ->
Golden Security Alarm -> \<serial number\>", corresponding entities
will be listed there.

| Option | Description |
|--------|-------------|
| Access point: enabled | Enable/disable the panel's WiFi access point functionality |
| Access point: Password | Password for the panel's WiFi access point |
| Alert: AC power failure | Enable/disable alert notifications when AC power fails |
| Alert: AC power recover | Enable/disable alert notifications when AC power is restored |
| Alert: Arm/disarm | Enable/disable alert notifications when panel is armed or disarmed |
| Alert: Door close | Enable/disable alert notifications when a door closes |
| Alert: Door open | Enable/disable alert notifications when a door opens |
| Alert: Host low voltage | Enable/disable alert notifications when the panel host has low battery voltage |
| Alert: Sensor low voltage | Enable/disable alert notifications when a sensor has low battery voltage |
| Alert: SMS push | Enable/disable SMS push notifications for alerts |
| Alert: WiFi available | Enable/disable alert notifications when WiFi becomes available |
| Alert: WiFi unavailable | Enable/disable alert notifications when WiFi becomes unavailable |
| Alarm: Phone 1 | First phone number to call when alarm is triggered |
| Alarm: Phone 2 | Second phone number to call when alarm is triggered |
| Alarm: Phone 3 | Third phone number to call when alarm is triggered |
| Alarm: Phone 4 | Fourth phone number to call when alarm is triggered |
| Alarm: Phone 5 | Fifth phone number to call when alarm is triggered |
| Alarm: Phone 6 | Sixth phone number to call when alarm is triggered |
| Alarm: SMS push phone 1 | First phone number to receive SMS push notifications |
| Alarm: SMS push phone 2 | Second phone number to receive SMS push notifications |
| Cellular: APN Authentication | Authentication method for cellular APN connection, provided by cellular operator |
| Cellular: APN Name | Access Point Name for cellular data connection, provided by cellular operator |
| Cellular: APN Password | Password for cellular APN authentication, provided by cellular operator |
| Cellular: APN User | Username for cellular APN authentication, provided by cellular operator |
| Cellular: enabled | Enable/disable cellular/GPRS connectivity |
| Delay: Alarm | Delay before the alarm sounds after a sensor is triggered |
| Delay: Arm | Delay before the panel arms after arming command |
| Duration: Alarm siren | Duration for how long the alarm siren will sound, use `0` to disable the siren |
| Duration: Backlight | Duration for how long the panel backlight stays on |
| Duration: Ring | Duration for how long the panel rings when receiving a call |
| Panel: Password | Panel password for disarming and remote control via SMS/calls |
| Panel: Phone number | The panel's own phone number, SIM card number for panels with cellular support |
| Simulate alerts from history | Enable/disable simulation of alerts from historical events |
| SMS alerts only when armed | When enabled, SMS alerts are only sent when the panel is armed |
| Speech: Language | Language and voice gender for panel speech announcements |
| Timezone offset | Timezone offset from UTC for the panel's internal clock |
| Volume: Alarm | Volume level for built-in alarm siren (Mute/Low/High) |
| Volume: Key tone | Volume level for keypad button press sounds (Mute/Low/High) |
| Volume: Ring | Volume level for incoming call (Mute/Low/High), only available on panels with cellular support |
| Volume: Speech | Volume level for speech announcements (Mute/Low/High) |

## Notifications

Notifications from the alarm panel are essential for the integration -
the notifications allow to reflect sensor and panel states change as they occurs.

The integration supports several protocols for the notifications:
* Local protocol (the default)
* Cloud protocol
* Cloud protocol with chaining

Please see below for the details on each.

### Local notifications protocol

For the protocol to be active at the alarm panel the device should have its IP
address set to `10.10.10.250`. That is a specific limitation of how device's
firmware works.

Additionally, the protocol implies the cloud servers are operational - missing
or delayed notifications with this protocol have been seen when vendor's cloud
servers are inoperational. Presumably, device takes cloud communications with
higher priority and doesn't get to local notifications protocol if cloud
communications are slow or timing out.

If your alarm panel is in a subnet different from one Home Assistant runs,
making the integration receiving the local notification messages will
require additional steps - the notifications are sent by alarm panel as
broadcast packets, thus you'll need those forwarded to the Home Assistant
subnet. Alternatively, you could consider the alert simulation or a different
protocol below.

### Cloud notifications protocol

Despite its name the procotol does not depend on any Internet connectivity
(unless using the chained mode below), the integration just implements same
protocol the panel uses to communicate with cloud servers - the devices is
"tricked" into thinking it is still communicating with the cloud servers,
while actual communication happens with the integration.

With this protocol it is no longer required for the alarm panel to have
`10.10.10.250` IP address. However, the protocol requires re-routing network
traffic coming from alarm panel to cloud servers to reach Home Assitant instance
insted. The re-routing could be done using DNAT (Destination Network
Address Translation), port mapping or similar techniques your network gear is
capable of.

Principle of the re-routing is as follows:

* For all TCP traffic
  * From: alarm panel
  * To: cloud servers and corresponding port - `47.88.7.61` and `5678` as of writing,
    respectively
* Change destination to
  * Home Assistant IP address and
  * Cloud notifications port configured in integration's options - `5678` by default

Please consult with your network equipment's documentation on how to implement that.

As the result, no alarm panel's traffic will be sent to vendor's cloud servers - they
will consider the panel being offline, so does the mobile application.

### Cloud notifications with chaining

It works similar to [Cloud notifications protocol](#cloud-notifications-protocol), but
also sends a copy of each notification up to vendor's cloud servers.
Thus, it does depend on Internet connectivity and the cloud servers to be operational,
but allows the mobile application to function normally.

The integration will still properly reflect sensor and panel state changes even
if cloud servers are down, it won't just send notifications copy there for
apparent reasons.

Traffic re-routing principles described in
[Cloud notifications protocol](#cloud-notifications-protocol) apply.
Depending on your network equipment sending the notifications copy to cloud servers
might result in a loop, so you'll need another rule configured:

* For all TCP traffic
  * From: Home Assistant instance
  * To: an arbitrary IP address in your network and port configured in the integration
    options
* Change destination to
  * Cloud servers and corresponding port - `47.88.7.61` and `5678` as of writing,
    respectively

You may also avoid the loop by configuring a port for cloud servers to send
traffic to different from `5678`, and using it to match the rule above. 

### Quick guide on selecting notifications protocol

* Use local notifications protocol if
  * You can assing the alarm panel `10.10.10.250` IP address and
  * You are ok to have sensors not reflecting state change when cloud server
    are down

* Use cloud notifications protocol if
  * You cannot assing the alarm panel `10.10.10.250` IP address or
  * You do not want sensors not reflecting their state when cloud servers
    are down
  * You are ok to have mobile application showing the panel as offline

* Use cloud notifications protocol with chaining if
  * You cannot assing the alarm panel `10.10.10.250` IP address or
  * Do not want sensors not reflecting their state when cloud servers
    are down 
  * Would like the mobile application to work normally

If none above works for you - the integration supports simulating the
device alerts from the history it records. It is implemented by
[pyg90alarm](https://pypi.org/project/pyg90alarm/) Python package, and it does
so by periodically polling the device history and sending newer entries down
the code path as if those been received from device.
The mode is enabled by selecting `Simulate device alerts from history` option
in integration configuration, and enabling particular alert types you're
interested in via mobile application.
This mode will still have limitations as not reflecting the state of motion
sensors (as those come as notifications not alerts).

If no notifications protocols are possible still, the integration will have
additional limitations:
* Delays reflecting panel status up to 30 seconds
* Sensor state changes will be absent

### Diagnostic sensors

To help diagnosing if notifications protocol is working properly the integration
exposes additional sensors:

* Last device packet time: indicates the time when integration successfully
  processed the last notification from the panel
* Last upstream packet time: indicates the time when cloud servers responded
  to a copy of notification the integration sent - the sensor is only applicable
  when using cloud notifications protocol with chaining


## Installation

* Install HACS by following [Setup](https://hacs.xyz/docs/setup/prerequisites)
  and [Configuration](https://hacs.xyz/docs/configuration/basic) steps
* Download `Golden Security Alarm` integration in HACS
* Add the `Golden Security Alarm` integration in Home Assistant


## Troubleshooting

If you need to troubleshoot the integration it is recommended to first enable
debug logging for it, to capture additional details.

For that you'll need to add following options to Home Assistant's
`configuration.yaml`. Please note this will also set logging level to `info`
for all other Home Assistant components - please adjust `default: info` to fit
your needs.

```
logger:
  default: info
  logs:
    pyg90alarm: debug
    homeassistant.gs_alarm: debug
    custom_components.gs_alarm: debug
```
