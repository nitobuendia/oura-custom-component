"""Proivdes an activity sensor."""

import logging
import voluptuous as vol
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import sensor_base

# Sensor configuration
_DEFAULT_NAME = 'oura_activity'

CONF_KEY_NAME = 'activity'
_DEFAULT_MONITORED_VARIABLES = [
    'active_calories',
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

# There is no need to add any configuration as all fields are optional and
# with default values. However, this is done as it is used in the main sensor.
DEFAULT_CONFIG = {}

_EMPTY_SENSOR_ATTRIBUTE = {
    'class_5_min': None,
    'score': None,
    'active_calories': None,
    'average_met_minutes': None,
    'day': None,
    'meet_daily_targets': None,
    'move_every_hour': None,
    'recovery_time': None,
    'stay_active': None,
    'training_frequency': None,
    'training_volume': None,
    'equivalent_walking_distance': None,
    'high_activity_met_minutes': None,
    'high_activity_time': None,
    'inactivity_alerts': None,
    'low_activity_met_minutes': None,
    'low_activity_time': None,
    'medium_activity_met_minutes': None,
    'medium_activity_time': None,
    'met': None,
    'meters_to_target': None,
    'non_wear_time': None,
    'resting_time': None,
    'sedentary_met_minutes': None,
    'sedentary_time': None,
    'steps': None,
    'target_calories': None,
    'target_meters': None,
    'timestamp': None,
    'total_calories': None,
}


class OuraActivitySensor(sensor_base.OuraDatedSensor):
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

    self._empty_sensor = _EMPTY_SENSOR_ATTRIBUTE
    self._main_state_attribute = 'score'

  def get_sensor_data_from_api(self, start_date, end_date):
    """Fetches activity data from the API.

    Args:
      start_date: Start date in YYYY-MM-DD.
      end_date: End date in YYYY-MM-DD.

    Returns:
      JSON object with API data.
    """
    return self._api.get_activity_data(start_date, end_date)

  def parse_sensor_data(self, oura_data):
    """Processes activity data into a dictionary.

    Args:
      oura_data: Readiness data in list format from Oura API.

    Returns:
      Dictionary where key is the requested summary_date and value is the
      Oura activity data for that given day.
    """
    if not oura_data or 'data' not in oura_data:
      logging.error(
          f'Oura ({self._name}): Couldn\'t fetch data for Oura ring sensor.')
      return {}

    activity_data = oura_data.get('data')
    if not activity_data:
      return {}

    activity_dict = {}
    for activity_daily_data in activity_data:
      # Default metrics.
      activity_date = activity_daily_data.get('day')
      if not activity_date:
        continue

      contributors = activity_daily_data.get('contributors', {})
      activity_daily_data.update(contributors)
      del activity_daily_data['contributors']

      activity_dict[activity_date] = activity_daily_data

    return activity_dict
