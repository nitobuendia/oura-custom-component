"""Provides a sleep sensor."""

import logging
import voluptuous as vol

from dateutil import parser
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import sensor_base
from .helpers import date_helper

# Sensor configuration
_DEFAULT_NAME = 'oura_sleep'

_DEFAULT_MONITORED_VARIABLES = [
    'average_breath',
    'average_heart_rate',
    'awake_duration_in_hours',
    'bedtime_start_hour',
    'bedtime_end_hour',
    'day',
    'deep_sleep_duration_in_hours',
    'in_bed_duration_in_hours',
    'light_sleep_duration_in_hours',
    'lowest_heart_rate',
    'rem_sleep_duration_in_hours',
    'total_sleep_duration_in_hours',
]
_SUPPORTED_MONITORED_VARIABLES = [
    'average_breath',
    'average_heart_rate',
    'average_hrv',
    'day',
    'awake_time',
    'awake_duration_in_hours',
    'awake_duration',
    'bedtime_end',
    'bedtime_end_hour',
    'bedtime_start',
    'bedtime_start_hour',
    'deep_sleep_duration',
    'deep_sleep_duration_in_hours',
    'efficiency',
    'heart_rate',
    'hrv',
    'in_bed_duration_in_hours',
    'latency',
    'light_sleep_duration',
    'light_sleep_duration_in_hours',
    'low_battery_alert',
    'lowest_heart_rate',
    'movement_30_sec',
    'period',
    'readiness_score_delta',
    'rem_sleep_duration',
    'rem_sleep_duration_in_hours',
    'restless_periods',
    'sleep_phase_5_min',
    'sleep_score_delta',
    'time_in_bed',
    'total_sleep_duration',
    'total_sleep_duration_in_hours',
    'type',
]

CONF_KEY_NAME = 'sleep'
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
    variable: None for variable in _SUPPORTED_MONITORED_VARIABLES
}


class OuraSleepSensor(sensor_base.OuraDatedSensor):
  """Representation of an Oura Ring Sleep sensor.

  Attributes:
    name: name of the sensor.
    state: state of the sensor.
    extra_state_attributes: attributes of the sensor.

  Methods:
    async_update: updates sensor data.
  """

  def __init__(self, config, hass):
    """Initializes the sensor."""
    sleep_config = config.get(const.CONF_SENSORS, {}).get(CONF_KEY_NAME, {})
    super(OuraSleepSensor, self).__init__(config, hass, sleep_config)

    self._empty_sensor = _EMPTY_SENSOR_ATTRIBUTE
    self._main_state_attribute = 'efficiency'

  def get_sensor_data_from_api(self, start_date, end_date):
    """Fetches sleep data from the API.

    Args:
      start_date: Start date in YYYY-MM-DD.
      end_date: End date in YYYY-MM-DD.

    Returns:
      JSON object with API data.
    """
    return self._api.get_sleep_data(start_date, end_date)

  def parse_sensor_data(self, oura_data):
    """Processes sleep data into a dictionary.

    Args:
      oura_data: Sleep data in list format from Oura API.

    Returns:
      Dictionary where key is the requested summary_date and value is the
      Oura sleep data for that given day.
    """
    if not oura_data or 'data' not in oura_data:
      logging.error(
          f'Oura ({self._name}): Couldn\'t fetch data for Oura ring sensor.')
      return {}

    sleep_data = oura_data.get('data')
    if not sleep_data:
      return {}

    sleep_dict = {}
    for sleep_daily_data in sleep_data:
      # Default metrics.
      sleep_date = sleep_daily_data.get('day')
      if not sleep_date:
        continue
      sleep_dict[sleep_date] = sleep_daily_data

      bedtime_start = parser.parse(sleep_daily_data.get('bedtime_start'))
      bedtime_end = parser.parse(sleep_daily_data.get('bedtime_end'))

      # Derived metrics.
      sleep_dict[sleep_date].update({
          # HH:MM at which you went bed.
          'bedtime_start_hour': bedtime_start.strftime('%H:%M'),
          # HH:MM at which you woke up.
          'bedtime_end_hour': bedtime_end.strftime('%H:%M'),
          # Hours in deep sleep.
          'deep_sleep_duration_in_hours': date_helper.seconds_to_hours(
              sleep_daily_data.get('deep_sleep_duration')),
          # Hours in REM sleep.
          'rem_sleep_duration_in_hours': date_helper.seconds_to_hours(
              sleep_daily_data.get('rem_sleep_duration')),
          # Hours in light sleep.
          'light_sleep_duration_in_hours': date_helper.seconds_to_hours(
              sleep_daily_data.get('light_sleep_duration')),
          # Hours sleeping: deep + rem + light.
          'total_sleep_duration_in_hours': date_helper.seconds_to_hours(
              sleep_daily_data.get('total_sleep_duration')),
          # Hours awake.
          'awake_duration': date_helper.seconds_to_hours(
              sleep_daily_data.get('awake_time')),
          # Hours in bed: sleep + awake.
          'in_bed_duration_in_hours': date_helper.seconds_to_hours(
              sleep_daily_data.get('time_in_bed')),
      })

    return sleep_dict
