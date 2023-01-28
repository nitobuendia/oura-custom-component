"""Provides a sleep score sensor."""

import voluptuous as vol
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import api
from . import const as oura_const
from . import sensor_base_dated

# Sensor configuration
CONF_KEY_NAME = 'sleep_score'

_DEFAULT_NAME = 'oura_sleep_score'

_DEFAULT_ATTRIBUTE_STATE = 'score'

_DEFAULT_MONITORED_VARIABLES = [
    'day',
    'score',
]

_SUPPORTED_MONITORED_VARIABLES = [
    'day',
    'deep_sleep',
    'efficiency',
    'latency',
    'rem_sleep',
    'restfulness',
    'score',
    'timing',
    'timestamp',
    'total_sleep',
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


class OuraSleepScoreSensor(sensor_base_dated.OuraDatedSensor):
  """Representation of an Oura Ring Sleep Score sensor.

  Attributes:
    name: name of the sensor.
    state: state of the sensor.
    extra_state_attributes: attributes of the sensor.

  Methods:
    async_update: updates sensor data.
  """

  def __init__(self, config, hass):
    """Initializes the sensor."""
    sleep_score_config = (
        config.get(const.CONF_SENSORS, {}).get(CONF_KEY_NAME, {}))
    super(OuraSleepScoreSensor, self).__init__(
        config, hass, sleep_score_config)

    self._api_endpoint = api.OuraEndpoints.SLEEP_SCORE
    self._empty_sensor = _EMPTY_SENSOR_ATTRIBUTE

  def parse_individual_datapoint(self, datapoint):
    """Parses the individual day or datapoint.

    Args:
      datapoint: Object for an individual day or datapoint.

    Returns:
      Modified datapoint with right parsed data.
    """
    datapoint_copy = {}
    datapoint_copy.update(datapoint)

    contributors = datapoint_copy.get('contributors', {})
    datapoint_copy.update(contributors)
    del datapoint_copy['contributors']

    return datapoint_copy
