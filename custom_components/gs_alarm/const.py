"""Constants for the gs_alarm integration."""

DOMAIN = "gs_alarm"

# Configuration options
CONF_SMS_ALERT_WHEN_ARMED = "sms_alert_when_armed"
CONF_SIMULATE_ALERTS_FROM_HISTORY = "simulate_alerts_from_history"
CONF_IP_ADDR = "ip_addr"
CONF_CLOUD_LOCAL_PORT = "cloud_local_port"
CONF_CLOUD_UPSTREAM_HOST = "cloud_upstream_host"
CONF_CLOUD_UPSTREAM_PORT = "cloud_upstream_port"
CONF_NOTIFICATIONS_PROTOCOL = "notifications_protocol"

# Options for CONF_NOTIFICATIONS_PROTOCOL
CONF_OPT_NOTIFICATIONS_LOCAL = "local"
CONF_OPT_NOTIFICATIONS_CLOUD = "cloud"
CONF_OPT_NOTIFICATIONS_CLOUD_UPSTREAM = "cloud_upstream"
