# SPDX-License-Identifier: MIT
# Copyright (c) 2021 Ilia Sotnikov
"""Constants for the gs_alarm integration."""
from datetime import timedelta

DOMAIN = "gs_alarm"
MANUFACTURER = "Golden Security"

# Configuration options
CONF_IP_ADDR = "ip_addr"
CONF_CLOUD_IP = "cloud_ip"
CONF_CLOUD_PORT = "cloud_port"
CONF_CLOUD_LOCAL_PORT = "cloud_local_port"
CONF_CLOUD_UPSTREAM_HOST = "cloud_upstream_host"
CONF_CLOUD_UPSTREAM_PORT = "cloud_upstream_port"
CONF_NOTIFICATIONS_PROTOCOL = "notifications_protocol"

# Options for CONF_NOTIFICATIONS_PROTOCOL
CONF_OPT_NOTIFICATIONS_LOCAL = "local"
CONF_OPT_NOTIFICATIONS_CLOUD = "cloud"
CONF_OPT_NOTIFICATIONS_CLOUD_UPSTREAM = "cloud_upstream"

# Data update interval
SCAN_INTERVAL = timedelta(seconds=30)

# Notifications protocol binary sensor
NOTIFICATIONS_PROTOCOL_SENSOR_LAST_DEVICE_TIMESTAMP_ATTR = (
    'last_device_packet_timestamp'
)
NOTIFICATIONS_PROTOCOL_SENSOR_LAST_UPSTREAM_TIMESTAMP_ATTR = (
    'last_upstream_packet_timestamp'
)
NOTIFICATIONS_PROTOCOL_SENSOR_TTL = timedelta(minutes=2)
NOTIFICATIONS_PROTOCOL_SENSOR_UNRECORDED_ATTRIBUTES = frozenset({
    NOTIFICATIONS_PROTOCOL_SENSOR_LAST_DEVICE_TIMESTAMP_ATTR,
    NOTIFICATIONS_PROTOCOL_SENSOR_LAST_UPSTREAM_TIMESTAMP_ATTR,
})
