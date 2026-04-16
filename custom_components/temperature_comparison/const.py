"""Constants for the Temperature Comparison integration."""

DOMAIN = "temperature_comparison"

CONF_INSIDE_ENTITY = "inside_temperature_entity"
CONF_OUTSIDE_ENTITY = "outside_temperature_entity"
CONF_NAME = "name"
CONF_WEIGHT_OUTDOOR = "weight_outdoor_correction"
CONF_HISTORY_DAYS = "history_days"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_DATA_SOURCE = "data_source"
CONF_INFLUXDB_HOST = "influxdb_host"
CONF_INFLUXDB_PORT = "influxdb_port"
CONF_INFLUXDB_TOKEN = "influxdb_token"
CONF_INFLUXDB_ORG = "influxdb_org"
CONF_INFLUXDB_BUCKET = "influxdb_bucket"

DEFAULT_NAME = "Temperature Comparison"
DEFAULT_WEIGHT_OUTDOOR = 0.5
DEFAULT_HISTORY_DAYS = 7
DEFAULT_UPDATE_INTERVAL = 1800  # 30 minutes
DEFAULT_DATA_SOURCE = "recorder"  # "recorder" or "influxdb"
DEFAULT_INFLUXDB_PORT = 8086
DEFAULT_INFLUXDB_ORG = "home-assistant"
DEFAULT_INFLUXDB_BUCKET = "homeassistant"

DATA_SOURCE_RECORDER = "recorder"
DATA_SOURCE_INFLUXDB = "influxdb"
