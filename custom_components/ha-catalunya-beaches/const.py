"""Constants for ha-catalunya-beaches."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "Catalunya Beaches"
DOMAIN = "ha-catalunya-beaches"
VERSION = "1.0.0"
ATTRIBUTION = "Data provided by Agència Catalana de l'Aigua"

# API Configuration
API_BASE_URL = "https://aplicacions.aca.gencat.cat/platgescat2/agencia-catalana-del-agua-backend/web/app.php/api"
API_BEACH_LIST = "/front/{language}"
API_BEACH_DETAIL = "/playadetalle/{beach_id}/{language}"
API_TIMEOUT = 30

# Update intervals (in seconds)
DEFAULT_UPDATE_INTERVAL = 3600  # 1 hour
MIN_UPDATE_INTERVAL = 900  # 15 minutes
MAX_UPDATE_INTERVAL = 86400  # 24 hours

# Configuration keys
CONF_BEACH_ID = "beach_id"
CONF_BEACH_NAME = "beach_name"
CONF_BEACH_LATITUDE = "beach_latitude"
CONF_BEACH_LONGITUDE = "beach_longitude"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_LANGUAGE = "language"
CONF_ENABLED_ENTITIES = "enabled_entities"

# Entity types
ENTITY_WATER_TEMP = "water_temperature"
ENTITY_AIR_TEMP = "air_temperature"
ENTITY_WATER_QUALITY = "water_quality"
ENTITY_UV_INDEX = "uv_index"
ENTITY_WAVE_HEIGHT = "wave_height"
ENTITY_WIND_SPEED = "wind_speed"
ENTITY_SKY_CONDITION = "sky_condition"
ENTITY_JELLYFISH_STATUS = "jellyfish_status"
ENTITY_LAST_TEST_DATE = "last_test_date"
ENTITY_DESCRIPTION = "description"
ENTITY_BEACH_INFO = "beach_info"
ENTITY_BEACH_NAME = "beach_name"
ENTITY_LIFEGUARD = "lifeguard_present"
ENTITY_OUT_OF_SEASON = "out_of_season"
ENTITY_WATER_QUALITY_GOOD = "water_quality_good"
ENTITY_JELLYFISH_ALERT = "jellyfish_alert"
ENTITY_RAIN_RISK = "rain_risk_high"

DEFAULT_ENABLED_ENTITIES = [
    ENTITY_WATER_TEMP,
    ENTITY_AIR_TEMP,
    ENTITY_WATER_QUALITY,
    ENTITY_UV_INDEX,
    ENTITY_WAVE_HEIGHT,
    ENTITY_WIND_SPEED,
    ENTITY_SKY_CONDITION,
    ENTITY_JELLYFISH_STATUS,
    ENTITY_LAST_TEST_DATE,
    ENTITY_DESCRIPTION,
    ENTITY_BEACH_INFO,
    ENTITY_LIFEGUARD,
    ENTITY_OUT_OF_SEASON,
    ENTITY_WATER_QUALITY_GOOD,
    ENTITY_JELLYFISH_ALERT,
    ENTITY_RAIN_RISK,
]

# API code translations
SAND_TYPES = {
    "_CODOL_": "Pebbles",
    "_SORRA_FINA_": "Fine sand",
    "_SORRA_MITJANA_": "Medium sand",
    "_SORRA_GRUIXUDA_": "Coarse sand",
    "_SORRA_MOLT_GRUIXUDA_": "Very coarse sand",
}

SKY_CONDITIONS = {
    "_1_": "Clear sky",
    "_3_": "Partly cloudy",
    "_20_": "Moderate to high cloud cover",
    "_21_": "Cloudy",
}

WATER_QUALITY_STATUS = {
    "_FORA_DE_TEMPORADA_": "Out of season",
    "Out of season": "Out of season",
    "Excellent": "Excellent",
    "Good": "Good",
    "Sufficient": "Acceptable",
    "Acceptable": "Acceptable",
    "Poor": "Poor",
    "Very Poor": "Very Poor",
    "Temporary disturbance (Rain)": "Acceptable",
    "Temporary disturbance": "Acceptable",
    "Persistence of temporary disturbance": "Poor",
}

JELLYFISH_STATUS = {
    "_FORA_DE_TEMPORADA_": "Out of season",
    "Out of season": "Out of season",
    "None": "None",
    "Low": "Low",
    "Moderate": "Moderate",
    "High": "High",
    "Very High": "Very High",
    "Unknown": "Unknown",
}

LIFEGUARD_STATUS = {
    "_SI_": True,
    "_NO_": False,
}

RISK_LEVELS = {
    "High": "high",
    "Medium": "medium",
    "Low": "low",
}
