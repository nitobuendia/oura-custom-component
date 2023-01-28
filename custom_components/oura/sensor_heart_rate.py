"""Provides a heart rate sensor."""

import datetime
import voluptuous as vol
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from . import api
from . import const as oura_const
from . import sensor_base_dated_series

# Sensor configuration
CONF_KEY_NAME = 'heart_rate'

_DEFAULT_NAME = 'oura_heart_rate'

_DEFAULT_ATTRIBUTE_STATE = 'bpm'

_DEFAULT_MONITORED_VARIABLES = [
    'day',
    'bpm',
    'source',
    'timestamp',
]

_SUPPORTED_MONITORED_VARIABLES = [
    'day',
    'bpm',
    'source',
    'timestamp',
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


class OuraHeartRateSensor(sensor_base_dated_series.OuraDatedSeriesSensor):
  """Representation of an Oura Ring Heart Rate sensor.

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
    super(OuraHeartRateSensor, self).__init__(config, hass, sessions_config)

    self._api_endpoint = api.OuraEndpoints.HEART_RATE
    self._empty_sensor = _EMPTY_SENSOR_ATTRIBUTE
    self._sort_key = 'timestamp'

  def get_sensor_data_from_api(self, start_date, end_date):
    """Fetches data from the API for the sensor.

    Args:
      start_date: Start date in YYYY-MM-DD.
      end_date: End date in YYYY-MM-DD.

    Returns:
      JSON object with API data.
    """
    start_date_parsed = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    start_date_parsed = start_date_parsed.replace(
        hour=0,
        minute=0,
        second=0,
    )
    start_time = start_date_parsed.isoformat()

    end_date_parsed = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    end_date_parsed = end_date_parsed.replace(
        hour=23,
        minute=59,
        second=59,
    )
    end_time = end_date_parsed.isoformat()

    return self._api.get_oura_data(self._api_endpoint, start_time, end_time)

  def parse_individual_data_point(self, data_point):
    """Parses the individual day or data point.

    Args:
      data_point: Object for an individual day or data point.

    Returns:
      Modified data point with right parsed data.
    """
    data_point_copy = {}
    data_point_copy.update(data_point)

    timestamp = data_point_copy.get('timestamp')
    if timestamp:
      parsed_timestamp = datetime.datetime.fromisoformat(timestamp)
      day = parsed_timestamp.strftime('%Y-%m-%d')
      data_point_copy['day'] = day

    return data_point_copy
