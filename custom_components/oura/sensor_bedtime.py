"""Provides a bedtime sensor."""

import logging
import voluptuous as vol
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import sensor_base
from .helpers import date_helper

# Sensor configuration
_DEFAULT_NAME = 'oura_bedtime'

CONF_KEY_NAME = 'bedtime'
_DEFAULT_MONITORED_VARIABLES = [
    'bedtime_window_start',
    'bedtime_window_end',
    'day',
]
_SUPPORTED_MONITORED_VARIABLES = [
    'bedtime_window_start',
    'bedtime_window_end',
    'day',
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

DEFAULT_CONFIG = {
    const.CONF_NAME: None,
    sensor_base.CONF_MONITORED_DATES: None,
    const.CONF_MONITORED_VARIABLES: None,

}

_EMPTY_SENSOR_ATTRIBUTE = {
    variable: None for variable in _SUPPORTED_MONITORED_VARIABLES
}


class OuraBedtimeSensor(sensor_base.OuraDatedSensor):
  """Representation of an Oura Ring Bedtime sensor.

  Attributes:
    name: name of the sensor.
    state: state of the sensor.
    extra_state_attributes: attributes of the sensor.

  Methods:
    async_update: updates sensor data.
  """

  def __init__(self, config, hass):
    """Initializes the sensor."""
    bedtime_config = (
        config.get(const.CONF_SENSORS, {}).get(CONF_KEY_NAME, {}))
    super(OuraBedtimeSensor, self).__init__(config, hass, bedtime_config)

    self._empty_sensor = _EMPTY_SENSOR_ATTRIBUTE
    self._main_state_attribute = 'bedtime_window_start'

  def get_sensor_data_from_api(self, start_date, end_date):
    """Fetches bedtime data from the API.

    Args:
      start_date: Start date in YYYY-MM-DD.
      end_date: End date in YYYY-MM-DD.

    Returns:
      JSON object with API data.
    """
    return self._api.get_bedtime_data(start_date, end_date)

  def parse_sensor_data(self, oura_data):
    """Processes bedtime data into a dictionary.

    Args:
      oura_data: Bedtime data in list format from Oura API.

    Returns:
      Dictionary where key is the requested summary_date and value is the
      Oura bedtime data for that given day.
    """
    if not oura_data or 'ideal_bedtimes' not in oura_data:
      logging.error(
          f'Oura ({self._name}): Couldn\'t fetch data for Oura ring sensor.')
      return {}

    bedtime_data = oura_data.get('ideal_bedtimes')
    if not bedtime_data:
      return {}

    bedtime_dict = {}
    for bedtime_daily_data in bedtime_data:
      # Default metrics.
      bedtime_date = bedtime_daily_data.get('date')
      if not bedtime_date:
        continue

      # Use day instead of date to bring consistency with V2 API.
      bedtime_daily_data['day'] = bedtime_date

      bedtime_window = bedtime_daily_data.get('bedtime_window', {})

      start_diff = bedtime_window['start']
      start_hour = date_helper.add_time_to_string_time('00:00', start_diff)
      bedtime_daily_data['bedtime_window_start'] = start_hour

      end_diff = bedtime_window['end']
      end_hour = date_helper.add_time_to_string_time('00:00', end_diff)
      bedtime_daily_data['bedtime_window_end'] = end_hour

      del bedtime_daily_data['bedtime_window']

      bedtime_dict[bedtime_date] = bedtime_daily_data

    return bedtime_dict
