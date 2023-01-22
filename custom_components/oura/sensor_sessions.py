"""Provides a sessions sensor."""

import voluptuous as vol
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import api
from . import sensor_base

# Sensor configuration
CONF_KEY_NAME = 'sessions'

_DEFAULT_NAME = 'oura_sessions'

_DEFAULT_ATTRIBUTE_STATE = 'type'

_DEFAULT_MONITORED_VARIABLES = [
    'day',
    'start_datetime',
    'end_datetime',
    'type',
    'heart_rate',
    'motion_count',
]

_SUPPORTED_MONITORED_VARIABLES = [
    'day',
    'start_datetime',
    'end_datetime',
    'type',
    'heart_rate',
    'heart_rate_variability',
    'mood',
    'motion_count',
]

CONF_SCHEMA = {
    vol.Optional(const.CONF_NAME, default=_DEFAULT_NAME): cv.string,

    vol.Optional(
        sensor_base.CONF_ATTRIBUTE_STATE,
        default=_DEFAULT_ATTRIBUTE_STATE
    ): vol.In(_SUPPORTED_MONITORED_VARIABLES),

    vol.Optional(
        sensor_base.CONF_MONITORED_DATES,
        default=sensor_base.DEFAULT_MONITORED_DATES
    ): cv.ensure_list,

    vol.Optional(
        const.CONF_MONITORED_VARIABLES,
        default=_DEFAULT_MONITORED_VARIABLES
    ): vol.All(cv.ensure_list, [vol.In(_SUPPORTED_MONITORED_VARIABLES)]),

    vol.Optional(
        sensor_base.CONF_BACKFILL,
        default=sensor_base.DEFAULT_BACKFILL
    ): cv.positive_int,
}

_EMPTY_SENSOR_ATTRIBUTE = {
    variable: None for variable in _SUPPORTED_MONITORED_VARIABLES
}


class OuraSessionsSensor(sensor_base.OuraDatedSeriesSensor):
  """Representation of an Oura Ring Sessions sensor.

  Attributes:
    name: name of the sensor.
    state: state of the sensor.
    extra_state_attributes: attributes of the sensor.

  Methods:
    async_update: updates sensor data.
  """

  def __init__(self, config, hass):
    """Initializes the sensor."""
    sessions_config = (
        config.get(const.CONF_SENSORS, {}).get(CONF_KEY_NAME, {}))
    super(OuraSessionsSensor, self).__init__(config, hass, sessions_config)

    self._api_endpoint = api.OuraEndpoints.SESSIONS
    self._empty_sensor = _EMPTY_SENSOR_ATTRIBUTE
