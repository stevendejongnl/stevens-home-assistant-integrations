"""Constants for the Temperature Comparison integration."""

DOMAIN = "temperature_comparison"

CONF_INSIDE_ENTITY = "inside_temperature_entity"
CONF_OUTSIDE_ENTITY = "outside_temperature_entity"
CONF_NAME = "name"
CONF_WEIGHT_OUTDOOR = "weight_outdoor_correction"
CONF_HISTORY_DAYS = "history_days"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_DATA_SOURCE = "data_source"

DEFAULT_NAME = "Temperature Comparison"
DEFAULT_WEIGHT_OUTDOOR = 0.5
DEFAULT_HISTORY_DAYS = 7
DEFAULT_UPDATE_INTERVAL = 1800  # 30 minutes
DEFAULT_DATA_SOURCE = "recorder"  # "recorder" or "influxdb"

DATA_SOURCE_RECORDER = "recorder"
DATA_SOURCE_INFLUXDB = "influxdb"
