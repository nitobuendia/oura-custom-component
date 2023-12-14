"""Provides an activity sensor."""

import voluptuous as vol
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import api
from . import const as oura_const
from . import sensor_base_dated

# Sensor configuration
_DEFAULT_NAME = 'oura_activity'

CONF_KEY_NAME = 'activity'
_DEFAULT_MONITORED_VARIABLES = [
    'active_calories',
    'day',
    'high_activity_time',
    'low_activity_time',
    'medium_activity_time',
    'non_wear_time',
    'resting_time',
    'sedentary_time',
    'score',
    'target_calories',
    'total_calories',
]
_SUPPORTED_MONITORED_VARIABLES = [
    'class_5_min',
    'score',
    'active_calories',
    'average_met_minutes',
    'day',
    'meet_daily_targets',
    'move_every_hour',
    'recovery_time',
    'stay_active',
    'training_frequency',
    'training_volume',
    'equivalent_walking_distance',
    'high_activity_met_minutes',
    'high_activity_time',
    'inactivity_alerts',
    'low_activity_met_minutes',
    'low_activity_time',
    'medium_activity_met_minutes',
    'medium_activity_time',
    'met',
    'meters_to_target',
    'non_wear_time',
    'resting_time',
    'sedentary_met_minutes',
    'sedentary_time',
    'steps',
    'target_calories',
    'target_meters',
    'timestamp',
    'total_calories',
]

CONF_SCHEMA = {
    vol.Optional(const.CONF_NAME, default=_DEFAULT_NAME): cv.string,

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


class OuraActivitySensor(sensor_base_dated.OuraDatedSensor):
  """Representation of an Oura Ring Activity sensor.

  Attributes:
    name: name of the sensor.
    state: state of the sensor.
    extra_state_attributes: attributes of the sensor.

  Methods:
    async_update: updates sensor data.
  """

  def __init__(self, config, hass):
    """Initializes the sensor."""
    activity_config = (
        config.get(const.CONF_SENSORS, {}).get(CONF_KEY_NAME, {}))
    super(OuraActivitySensor, self).__init__(config, hass, activity_config)

    self._api_endpoint = api.OuraEndpoints.ACTIVITY
    self._empty_sensor = _EMPTY_SENSOR_ATTRIBUTE
    self._main_state_attribute = 'score'

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
