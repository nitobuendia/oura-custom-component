"""Provides a workouts sensor."""

import voluptuous as vol
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import api
from . import const as oura_const
from . import sensor_base_dated_series

# Sensor configuration
CONF_KEY_NAME = 'workouts'

_DEFAULT_NAME = 'oura_workouts'

_DEFAULT_ATTRIBUTE_STATE = 'activity'

_DEFAULT_MONITORED_VARIABLES = [
    'activity',
    'calories',
    'day',
    'intensity',
]

_SUPPORTED_MONITORED_VARIABLES = [
    'activity',
    'calories',
    'day',
    'distance',
    'end_datetime',
    'intensity',
    'label',
    'source',
    'start_datetime',
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


class OuraWorkoutsSensor(sensor_base_dated_series.OuraDatedSeriesSensor):
  """Representation of an Oura Ring Workouts sensor.

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
    super(OuraWorkoutsSensor, self).__init__(config, hass, sessions_config)

    self._api_endpoint = api.OuraEndpoints.WORKOUTS
    self._empty_sensor = _EMPTY_SENSOR_ATTRIBUTE
