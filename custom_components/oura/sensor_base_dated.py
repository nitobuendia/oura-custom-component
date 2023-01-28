"""Provides a base OuraSensor class for dated Oura endpoints."""

import datetime
import enum
import logging
import re
from homeassistant import const
from . import const as oura_const
from . import sensor_base
from .helpers import date_helper


class MonitoredDayType(enum.Enum):
  """Types of days which can be monitored."""
  UNKNOWN = 0
  YESTERDAY = 1
  WEEKDAY = 2
  DAYS_AGO = 3


_FULL_WEEKDAY_NAMES = [
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
    'sunday',
]


class OuraDatedSensor(sensor_base.OuraSensor):
  """Representation of an Oura Ring sensor with daily data.

  Attributes:
    name: name of the sensor.
    state: state of the sensor.
    extra_state_attributes: attributes of the sensor.

  Methods:
    filter_individual_data_point: Filters a data point from the API.
    get_sensor_data_from_api: Fetches data from the API.
    parse_individual_data_point: Parses a data point from the API.
    parse_sensor_data: Parses data from the API.
  """

  def __init__(self, config, hass, sensor_config=None):
    """Initializes the sensor.

    Args:
      config: Platform configuration.
      hass: Home-Assistant object.
      sensor_config: Sub-section of config holding the particular sensor info.
    """
    super(OuraDatedSensor, self).__init__(config, hass)

    # Dated sensor config.
    if not sensor_config:
      sensor_config = config
    self._sensor_config.update(sensor_config)

    self._name = self._sensor_config.get(const.CONF_NAME)
    self._backfill = self._sensor_config.get(oura_const.CONF_BACKFILL)
    self._main_state_attribute = self._sensor_config.get(
        oura_const.CONF_ATTRIBUTE_STATE)

    self._monitored_variables = [
        variable_name.lower()
        for variable_name
        in self._sensor_config.get(const.CONF_MONITORED_VARIABLES)
    ] if self._sensor_config.get(const.CONF_MONITORED_VARIABLES) else []

    self._monitored_dates = [
        date_name.lower()
        for date_name
        in self._sensor_config.get(oura_const.CONF_MONITORED_DATES)
    ] if self._sensor_config.get(oura_const.CONF_MONITORED_DATES) else []

    # API endpoint for this sensor.
    self._api_endpoint = ''
    # Empty daily sensor data.
    self._empty_sensor = {}

  def _filter_monitored_variables(self, sensor_data):
    """Filters the sensor data to only contain monitored variables.

    Args:
      sensor_data: Map of dates to sensor data.

    Returns:
      Same sensor_data map but filtered to only contain monitored variables.
    """
    data = {}
    data.update(sensor_data)

    if not data:
      return data

    for date_attributes in list(data.values()):
      for variable in list(date_attributes.keys()):
        if variable not in self._monitored_variables:
          del date_attributes[variable]
    return data

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
      logging.info(
          f'Oura ({self._name}): ' +
          'Unknown day name `{date_name}`, using yesterday.')
      days_ago = 1

    return str(today - datetime.timedelta(days=days_ago))

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

  def _get_monitored_date_range(self):
    """Returns tuple containing start and end date based on monitored dates.

    Returns:
      (start_date, end_date) in YYYY-MM-DD
    """
    sensor_dates = self._get_monitored_name_days()

    today_date = datetime.datetime.today().strftime('%Y-%m-%d')
    sensor_dates = sensor_dates.values()
    start_date = (
        min(sensor_dates) if len(sensor_dates) > 0 else today_date)
    end_date = (
        max(sensor_dates) if len(sensor_dates) > 0 else today_date)

    # Add an extra week to retrieve past week in case current week data is
    # missing.
    start_date = date_helper.add_days_to_string_date(start_date, -7)

    # Add an extra day to retrieve today's date in case of timezone difference.
    end_date = date_helper.add_days_to_string_date(end_date, 1)

    return (start_date, end_date)

  def _get_monitored_name_days(self):
    """Gets the date name of all monitored days.

    Returns:
      Map of date names to dates (YYYY-MM-DD) for monitored days.
    """
    return {
        date_name: self._get_date_by_name(date_name)
        for date_name in self._monitored_dates
    }

  def _map_data_to_monitored_days(self, sensor_data, default_attributes=None):
    """Reads sensor data and maps it to the monitored dates, incl. backfill.

    Args:
      sensor_data: All parsed sensor data with daily breakdowns.
      default_attributes: Sensor information to use if no data is retrieved.

    Returns:
      sensor_data mapped to monitored_dates.
    """
    sensor_dates = self._get_monitored_name_days()
    (start_date, _) = self._get_monitored_date_range()

    if not sensor_data:
      sensor_data = {}

    if not default_attributes:
      default_attributes = {}

    dated_attributes_map = {}
    for date_name, date_value in sensor_dates.items():
      date_attributes = dict()
      date_attributes.update(default_attributes)
      date_attributes['day'] = date_value

      daily_data = sensor_data.get(date_value)
      date_name_title = date_name.title()

      # Check past dates to see if backfill is possible when missing data.
      backfill = 0
      original_date = date_value
      while (not daily_data
             and backfill < self._backfill
             and date_value >= start_date):
        date_value = self._get_backfill_date(date_name, date_value)
        if not date_value:
          break
        daily_data = sensor_data.get(date_value)
        backfill += 1

      if original_date != date_value:
        logging.warning(
            (
                f'Oura ({self._name}): No Oura data found for '
                f'{date_name_title} ({original_date}). Fetching {date_value} '
                'instead.'
            ) if date_value else (
                f'Unable to find suitable backfill date. No data available.'
            )
        )

      if daily_data:
        date_attributes.update(daily_data)

      dated_attributes_map[date_name] = date_attributes

    return dated_attributes_map

  def _update_state(self, sensor_attributes):
    """Updates the state based on the sensor attributes.

    Args:
      sensor_attributes: Sensor attributes (before filtering).
    """
    if not self._main_state_attribute:
      return

    if not self._monitored_dates:
      return

    first_monitored_date = self._monitored_dates[0]
    if not first_monitored_date:
      return

    first_date_attributes = sensor_attributes.get(first_monitored_date)
    if not first_date_attributes:
      return

    self._state = first_date_attributes.get(self._main_state_attribute)

  def _update(self):
    """Fetches new state data for the sensor."""
    (start_date, end_date) = self._get_monitored_date_range()

    oura_data = self.get_sensor_data_from_api(start_date, end_date)
    sensor_data = self.parse_sensor_data(oura_data)

    if not sensor_data:
      sensor_data = {}

    dated_attributes = self._map_data_to_monitored_days(
        sensor_data, self._empty_sensor)

    # Update state must happen before filtering for monitored variables.
    self._update_state(dated_attributes)

    dated_attributes = self._filter_monitored_variables(dated_attributes)
    self._attributes = dated_attributes

  def filter_individual_data_point(self, data_point):
    """Filters an individual data point.

    If data must be filtered, this must be implemented by the child class.

    Args:
      data_point: Object for an individual day or data point.

    Returns:
      True, if data needs to be included. False, otherwise.
    """
    return True

  def get_sensor_data_from_api(self, start_date, end_date):
    """Fetches data from the API for the sensor.

    Args:
      start_date: Start date in YYYY-MM-DD.
      end_date: End date in YYYY-MM-DD.

    Returns:
      JSON object with API data.
    """
    return self._api.get_oura_data(self._api_endpoint, start_date, end_date)

  def parse_individual_data_point(self, data_point):
    """Parses the individual day or data point.

    If there are changes to the data point, they must be implemented by child.

    Args:
      data_point: Object for an individual day or data point.

    Returns:
      Modified data point with right parsed data.
    """
    return data_point

  def parse_sensor_data(self, oura_data, data_param='data', day_param='day'):
    """Parses data from the API.

    Args:
      oura_data: Data from Oura API.
      data_param: Parameter where data is found. By default: 'data'.
      day_param: Parameter where date is found. By default: 'date'.

    Returns:
      Dictionary where key is the requested date and value is the
      Oura sensor data for that given day.
    """
    if not oura_data or data_param not in oura_data:
      logging.error(
          f'Oura ({self._name}): Couldn\'t fetch data for Oura ring sensor.')
      return {}

    sensor_data = oura_data.get(data_param)
    if not sensor_data:
      return {}

    sensor_dict = {}
    for sensor_daily_data in sensor_data:
      sensor_daily_data = self.parse_individual_data_point(sensor_daily_data)
      if not sensor_daily_data:
        continue

      include_in_data = self.filter_individual_data_point(sensor_daily_data)
      if not include_in_data:
        continue

      sensor_date = sensor_daily_data.get(day_param)
      if not sensor_date:
        continue

      sensor_dict[sensor_date] = sensor_daily_data

    return sensor_dict
