"""Provides a bedtime sensor."""

import voluptuous as vol
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import api
from . import const as oura_const
from . import sensor_base_dated
from .helpers import date_helper

# Sensor configuration
CONF_KEY_NAME = 'bedtime'

_DEFAULT_NAME = 'oura_bedtime'

_DEFAULT_ATTRIBUTE_STATE = 'bedtime_window_start'

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


class OuraBedtimeSensor(sensor_base_dated.OuraDatedSensor):
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

    self._api_endpoint = api.OuraEndpoints.BEDTIME
    self._empty_sensor = _EMPTY_SENSOR_ATTRIBUTE

  def parse_individual_data_point(self, data_point):
    """Parses the individual day or data point.

    Args:
      data_point: Object for an individual day or data point.

    Returns:
      Modified data point with right parsed data.
    """
    data_point_copy = {}
    data_point_copy.update(data_point)

    data_point_copy['day'] = data_point_copy['date']

    bedtime_window = data_point_copy.get('bedtime_window', {})

    start_diff = bedtime_window['start']
    start_hour = date_helper.add_time_to_string_time('00:00', start_diff)
    data_point_copy['bedtime_window_start'] = start_hour

    end_diff = bedtime_window['end']
    end_hour = date_helper.add_time_to_string_time('00:00', end_diff)
    data_point_copy['bedtime_window_end'] = end_hour

    del data_point_copy['bedtime_window']

    return data_point_copy

  def parse_sensor_data(self, oura_data):
    """Processes bedtime data into a dictionary.

    Args:
      oura_data: Bedtime data in list format from Oura API.

    Returns:
      Dictionary where key is the requested summary_date and value is the
      Oura bedtime data for that given day.
    """
    return super(OuraBedtimeSensor, self).parse_sensor_data(
        oura_data, 'ideal_bedtimes')
