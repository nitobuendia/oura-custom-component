"""Proivdes a readiness sensor."""

import logging
import voluptuous as vol
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import sensor_base

# Sensor configuration
_DEFAULT_NAME = 'oura_readiness'

CONF_KEY_NAME = 'readiness'
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
    'activity_balance': None,
    'body_temperature': None,
    'day': None,
    'hrv_balance': None,
    'previous_day_activity': None,
    'previous_night': None,
    'recovery_index': None,
    'resting_heart_rate': None,
    'score': None,
    'sleep_balance': None,
    'temperature_deviation': None,
    'temperature_trend_deviation': None,
    'timestamp': None,
}


class OuraReadinessSensor(sensor_base.OuraDatedSensor):
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

    self._empty_sensor = _EMPTY_SENSOR_ATTRIBUTE
    self._main_state_attribute = 'score'

  def get_sensor_data_from_api(self, start_date, end_date):
    """Fetches readiness data from the API.

    Args:
      start_date: Start date in YYYY-MM-DD.
      end_date: End date in YYYY-MM-DD.

    Returns:
      JSON object with API data.
    """
    return self._api.get_readiness_data(start_date, end_date)

  def parse_sensor_data(self, oura_data):
    """Processes readiness data into a dictionary.

    Args:
      oura_data: Readiness data in list format from Oura API.

    Returns:
      Dictionary where key is the requested summary_date and value is the
      Oura readiness data for that given day.
    """
    if not oura_data or 'data' not in oura_data:
      logging.error(
          f'Oura ({self._name}): Couldn\'t fetch data for Oura ring sensor.')
      return {}

    readiness_data = oura_data.get('data')
    if not readiness_data:
      return {}

    readiness_dict = {}
    for readiness_daily_data in readiness_data:
      # Default metrics.
      readiness_date = readiness_daily_data.get('day')
      if not readiness_date:
        continue

      contributors = readiness_daily_data.get('contributors', {})
      readiness_daily_data.update(contributors)
      del readiness_daily_data['contributors']

      readiness_dict[readiness_date] = readiness_daily_data

    return readiness_dict