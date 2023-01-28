"""Provides a base OuraSensor class for date-series Oura endpoints."""

import logging
from . import sensor_base_dated


class OuraDatedSeriesSensor(sensor_base_dated.OuraDatedSensor):
  """Representation of an Oura Ring sensor with series daily data.

  Attributes:
    name: name of the sensor.
    state: state of the sensor.
    extra_state_attributes: attributes of the sensor.

  Methods:
    async_update: updates sensor data.
  """

  def __init__(self, config, hass, sensor_config=None):
    """Initializes the sensor.

    Args:
      config: Platform configuration.
      hass: Home-Assistant object.
      sensor_config: Sub-section of config holding the particular sensor info.

    Methods:
      parse_sensor_data: Parses data from API.
    """
    super(OuraDatedSeriesSensor, self).__init__(config, hass, sensor_config)
    self._sort_key = 'start_datetime'

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

    for date_series in list(data.values()):
      for daily_data_point in date_series:
        for variable in list(daily_data_point.keys()):
          if variable not in self._monitored_variables:
            del daily_data_point[variable]
    return data

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
      date_values = []

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

      if not daily_data:
        daily_data = [self._empty_sensor]

      if not type(daily_data) == list:
        daily_data = [daily_data]

      for series_data in daily_data:
        series_attributes = dict()
        series_attributes.update(default_attributes)
        series_attributes['day'] = date_value
        series_attributes.update(series_data)
        date_values.append(series_attributes)

        if date_name not in dated_attributes_map:
          dated_attributes_map[date_name] = []

      dated_attributes_map[date_name].extend(date_values)

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

    first_date_attributes_copy = []
    first_date_attributes_copy.extend(first_date_attributes)
    sorted(
        first_date_attributes_copy,
        key=lambda data_point: data_point[self._sort_key])

    first_series_attribute = first_date_attributes_copy[0]
    if not first_series_attribute:
      return

    self._state = first_series_attribute.get(self._main_state_attribute)

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

      if sensor_date not in sensor_dict:
        sensor_dict[sensor_date] = []

      sensor_dict[sensor_date].append(sensor_daily_data)

    return sensor_dict
