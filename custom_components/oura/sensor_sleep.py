"""Provides a sleep sensor."""

import datetime
import enum
import logging
import re
import voluptuous as vol

from dateutil import parser
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import sensor_base
from .helpers import date_helper
from .helpers import math_helper

# Sensor configuration
_DEFAULT_NAME = 'oura_sleep'

_CONFIG_MONITORED_DATES = 'monitored_dates'
_DEFAULT_MONITORED_DATES = ['yesterday']

_DEFAULT_MONITORED_VARIABLES = [
    'average_breath',
    'average_heart_rate',
    'awake_time',
    'bedtime_start_hour',
    'bedtime_end_hour',
    'day',
    'deep_sleep_duration',
    'light_sleep_duration',
    'lowest_heart_rate',
    'rem_sleep_duration',
    'time_in_bed',
    'total_sleep_duration',
]
_SUPPORTED_MONITORED_VARIABLES = [
    'average_breath',
    'average_heart_rate',
    'average_hrv',
    'day',
    'awake_time',
    'bedtime_end',
    'bedtime_end_hour',
    'bedtime_start',
    'bedtime_start_hour',
    'deep_sleep_duration',
    'efficiency',
    'heart_rate',
    'heart_rate_average',
    'hrv',
    'latency',
    'light_sleep_duration',
    'low_battery_alert',
    'lowest_heart_rate',
    'movement_30_sec',
    'period',
    'readiness_score_delta',
    'rem_sleep_duration',
    'restless_periods',
    'sleep_phase_5_min',
    'sleep_score_delta',
    'time_in_bed',
    'total_sleep_duration',
    'type',
]

_CONF_BACKFILL = 'max_backfill'
_DEFAULT_BACKFILL = 0

CONF_KEY_NAME = 'sleep'
CONF_SCHEMA = {
    vol.Optional(const.CONF_NAME, default=_DEFAULT_NAME): cv.string,

    vol.Optional(
        _CONFIG_MONITORED_DATES,
        default=_DEFAULT_MONITORED_DATES
    ): cv.ensure_list,

    vol.Optional(
        const.CONF_MONITORED_VARIABLES,
        default=_DEFAULT_MONITORED_VARIABLES
    ): vol.All(cv.ensure_list, [vol.In(_SUPPORTED_MONITORED_VARIABLES)]),

    vol.Optional(
        _CONF_BACKFILL,
        default=_DEFAULT_BACKFILL
    ): cv.positive_int,
}

# There is no need to add any configuration as all fields are optional and
# with default values. However, this is done as it is used in the main sensor.
DEFAULT_CONFIG = {}

# Constants.
_FULL_WEEKDAY_NAMES = [
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
    'sunday',
]

_EMPTY_SENSOR_ATTRIBUTE = {
    'average_breath': None,
    'average_heart_rate': None,
    'average_hrv': None,
    'day': None,
    'awake_time': None,
    'bedtime_end': None,
    'bedtime_end_hour': None,
    'bedtime_start': None,
    'bedtime_start_hour': None,
    'deep_sleep_duration': None,
    'efficiency': None,
    'heart_rate': {
        'interval': None,
        'items': [],
        'timestamp': None,
    },
    'heart_rate_average': None,
    'hrv': {
        'interval': None,
        'items': [],
        'timestamp': None,
    },
    'latency': None,
    'light_sleep_duration': None,
    'low_battery_alert': None,
    'lowest_heart_rate': None,
    'movement_30_sec': None,
    'period': None,
    'readiness_score_delta': None,
    'rem_sleep_duration': None,
    'restless_periods': None,
    'sleep_phase_5_min': None,
    'sleep_score_delta': None,
    'time_in_bed': None,
    'total_sleep_duration': None,
    'type': None,
}


class MonitoredDayType(enum.Enum):
  """Types of days which can be monitored."""
  UNKNOWN = 0
  YESTERDAY = 1
  WEEKDAY = 2
  DAYS_AGO = 3


class OuraSleepSensor(sensor_base.OuraSensor):
  """Representation of an Oura Ring Sleep sensor.

  Attributes:
    name: name of the sensor.
    state: state of the sensor.
    extra_state_attributes: attributes of the sensor.

  Methods:
    async_update: updates sensor data.
    create_oauth_view: creates a view to manage OAuth setup.
  """

  def __init__(self, config, hass):
    """Initializes the sensor."""
    super(OuraSleepSensor, self).__init__(config, hass)

    # Sleep sensor config.
    sleep_config = config.get(const.CONF_SENSORS, {}).get(CONF_KEY_NAME, {})
    self._name = sleep_config.get(const.CONF_NAME)
    self._monitored_variables = [
        variable_name.lower()
        for variable_name in sleep_config.get(const.CONF_MONITORED_VARIABLES)
    ]
    self._monitored_dates = [
        date_name.lower()
        for date_name in sleep_config.get(_CONFIG_MONITORED_DATES)
    ]
    self._backfill = sleep_config.get(_CONF_BACKFILL)

  # Oura update logic.
  def _get_date_type_by_name(self, date_name):
    """Gets the type of date format based in the date name.

    Args:
      date_name: Date for which to verify type.

    Returns:
      Date type(MonitoredDayType).
    """
    if date_name == 'yesterday':
      return MonitoredDayType.YESTERDAY
    elif date_name in _FULL_WEEKDAY_NAMES:
      return MonitoredDayType.WEEKDAY
    elif 'd_ago' in date_name or 'days_ago' in date_name:
      return MonitoredDayType.DAYS_AGO
    else:
      return MonitoredDayType.UNKNOWN

  def _get_date_by_name(self, date_name):
    """Translates a date name into YYYY-MM-DD format for the given day.

    Args:
      date_name: Name of the date to get. Supported:
        yesterday, weekday(e.g. monday, tuesday), Xdays_ago(e.g. 3days_ago).

    Returns:
      Date in YYYY-MM-DD format.
    """
    date_type = self._get_date_type_by_name(date_name)
    today = datetime.date.today()
    days_ago = None
    if date_type == MonitoredDayType.YESTERDAY:
      days_ago = 1

    elif date_type == MonitoredDayType.WEEKDAY:
      date_index = _FULL_WEEKDAY_NAMES.index(date_name)
      days_ago = (
          today.weekday() - date_index
          if today.weekday() > date_index else
          7 + today.weekday() - date_index
      )

    elif date_type == MonitoredDayType.DAYS_AGO:
      digits_regex = re.compile(r'\d+')
      digits_match = digits_regex.match(date_name)
      if digits_match:
        try:
          days_ago = int(digits_match.group())
        except:
          days_ago = None

    if days_ago is None:
      logging.info(f'Oura: Unknown day name `{date_name}`, using yesterday.')
      days_ago = 1

    return str(today - datetime.timedelta(days=days_ago))

  def _get_backfill_date(self, date_name, date_value):
    """Gets the backfill date for a given date and date name.

    Args:
      date_name: Date name to backfill.
      date_value: Last checked value.

    Returns:
      Potential backfill date. None if Unknown.
    """
    date_type = self._get_date_type_by_name(date_name)

    if date_type == MonitoredDayType.YESTERDAY:
      return date_helper.add_days_to_string_date(date_value, -1)
    elif date_type == MonitoredDayType.WEEKDAY:
      return date_helper.add_days_to_string_date(date_value, -7)
    elif date_type == MonitoredDayType.DAYS_AGO:
      return date_helper.add_days_to_string_date(date_value, -1)
    else:
      return None

  def _parse_sleep_data(self, oura_data):
    """Processes sleep data into a dictionary.

    Args:
      oura_data: Sleep data in list format from Oura API.

    Returns:
      Dictionary where key is the requested summary_date and value is the
      Oura sleep data for that given day.
    """
    if not oura_data or 'data' not in oura_data:
      logging.error('Couldn\'t fetch data for Oura ring sensor.')
      return {}

    sleep_data = oura_data.get('data')
    if not sleep_data:
      return {}

    sleep_dict = {}
    for sleep_daily_data in sleep_data:
      sleep_date = sleep_daily_data.get('day')
      if not sleep_date:
        continue
      sleep_dict[sleep_date] = sleep_daily_data

    return sleep_dict

  def _update(self):
    """Fetches new state data for the sensor."""
    sleep_dates = {
        date_name: self._get_date_by_name(date_name)
        for date_name in self._monitored_dates
    }

    # Add an extra week to retrieve past week in case current week data is
    # missing.
    start_date = date_helper.add_days_to_string_date(
        min(sleep_dates.values()), -7)
    end_date = max(sleep_dates.values())

    oura_data = self._api.get_sleep_data(start_date, end_date)
    sleep_data = self._parse_sleep_data(oura_data)

    if not sleep_data:
      return

    for date_name, date_value in sleep_dates.items():
      if date_name not in self._attributes:
        self._attributes[date_name] = dict()
        self._attributes[date_name].update(_EMPTY_SENSOR_ATTRIBUTE)
        self._attributes[date_name]['day'] = date_value

      sleep = sleep_data.get(date_value)
      date_name_title = date_name.title()

      # Check past dates to see if backfill is possible when missing data.
      backfill = 0
      original_date = date_value
      while (not sleep
             and backfill < self._backfill
             and date_value >= start_date):
        date_value = self._get_backfill_date(date_name, date_value)
        if not date_value:
          break
        sleep = sleep_data.get(date_value)
        backfill += 1

      if original_date != date_value:
        logging.warning(
            f'No Oura data found for {date_name_title} ({original_date}). ' +
            (
                f'Fetching {date_value} instead.'
                if date_value else
                f'Unable to find suitable backfill date. No data available.'
            )
        )

      if not sleep:
        continue

      # State gets the value of the sleep score for the first monitored day.
      if self._monitored_dates.index(date_name) == 0:
        self._state = sleep.get('efficiency')

      bedtime_start = parser.parse(sleep.get('bedtime_start'))
      bedtime_end = parser.parse(sleep.get('bedtime_end'))

      heart_rates = sleep.get('heart_rate', {}).get('items', [])

      self._attributes[date_name].update(sleep)
      self._attributes[date_name].update({
          # HH:MM at which you went bed.
          'bedtime_start_hour': bedtime_start.strftime('%H:%M'),
          # HH:MM at which you woke up.
          'bedtime_end_hour': bedtime_end.strftime('%H:%M'),
          # Avg. beats / minute.
          'heart_rate_average': math_helper.safe_average(heart_rates),
          # Hours in deep sleep.
          'deep_sleep_duration': date_helper.seconds_to_hours(
              sleep.get('deep_sleep_duration')),
          # Hours in REM sleep.
          'rem_sleep_duration': date_helper.seconds_to_hours(
              sleep.get('rem_sleep_duration')),
          # Hours in light sleep.
          'light_sleep_duration': date_helper.seconds_to_hours(
              sleep.get('light_sleep_duration')),
          # Hours sleeping: deep + rem + light.
          'total_sleep_duration': date_helper.seconds_to_hours(
              sleep.get('total_sleep_duration')),
          # Hours awake.
          'awake_duration': date_helper.seconds_to_hours(
              sleep.get('awake_time')),
          # Hours in bed: sleep + awake.
          'in_bed_duration': date_helper.seconds_to_hours(
              sleep.get('time_in_bed')),
      })
