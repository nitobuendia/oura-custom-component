"""Provides a readiness sensor."""

import voluptuous as vol
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import api
from . import const as oura_const
from . import sensor_base_dated

# Sensor configuration
CONF_KEY_NAME = 'readiness'

_DEFAULT_NAME = 'oura_readiness'

_DEFAULT_ATTRIBUTE_STATE = 'score'

_DEFAULT_MONITORED_VARIABLES = [
    'activity_balance',
    'body_temperature',
    'hrv_balance',
    'previous_day_activity',
    'previous_night',
    'day',
    'recovery_index',
    'resting_heart_rate',
    'score',
    'sleep_balance',
]

_SUPPORTED_MONITORED_VARIABLES = [
    'activity_balance',
    'body_temperature',
    'day',
    'hrv_balance',
    'previous_day_activity',
    'previous_night',
    'recovery_index',
    'resting_heart_rate',
    'sleep_balance',
    'score',
    'temperature_deviation',
    'temperature_trend_deviation',
    'timestamp',
]

CONF_SCHEMA = {
    vol.Optional(const.CONF_NAME, default=_DEFAULT_NAME): cv.string,

    vol.Optional(
        oura_const.CONF_ATTRIBUTE_STATE,
        default=_DEFAULT_ATTRIBUTE_STATE
    ): vol.In(_SUPPORTED_MONITORED_VARIABLES),

    vol.Optional(
        oura_const.CONF_MONITORED_DATES,
        default=oura_const.DEFAULT_MONITORED_DATES
    ): cv.ensure_list,

    vol.Optional(
        const.CONF_MONITORED_VARIABLES,
        default=_DEFAULT_MONITORED_VARIABLES
    ): vol.All(cv.ensure_list, [vol.In(_SUPPORTED_MONITORED_VARIABLES)]),

    vol.Optional(
        oura_const.CONF_BACKFILL,
        default=oura_const.DEFAULT_BACKFILL
    ): cv.positive_int,
}

_EMPTY_SENSOR_ATTRIBUTE = {
    variable: None for variable in _SUPPORTED_MONITORED_VARIABLES
}


class OuraReadinessSensor(sensor_base_dated.OuraDatedSensor):
  """Representation of an Oura Ring Readiness sensor.

  Attributes:
    name: name of the sensor.
    state: state of the sensor.
    extra_state_attributes: attributes of the sensor.

  Methods:
    async_update: updates sensor data.
  """

  def __init__(self, config, hass):
    """Initializes the sensor."""
    readiness_config = (
        config.get(const.CONF_SENSORS, {}).get(CONF_KEY_NAME, {}))
    super(OuraReadinessSensor, self).__init__(config, hass, readiness_config)

    self._api_endpoint = api.OuraEndpoints.READINESS
    self._empty_sensor = _EMPTY_SENSOR_ATTRIBUTE

  def parse_individual_data_point(self, data_point):
    """Parses the individual day or data point.

    Args:
      data_point: Object for an individual day or data point.

    Returns:
      Modified data point with right parsed data.
    """
    data_point_copy = {}
    data_point_copy.update(data_point)

    contributors = data_point_copy.get('contributors', {})
    data_point_copy.update(contributors)
    del data_point_copy['contributors']

    return data_point_copy
