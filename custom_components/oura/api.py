"""Provides an OuraApi class to handle interactions with Oura API."""

import enum
import requests
from .helpers import hass_helper

# Oura API config.
_OURA_API_V1 = 'https://api.ouraring.com/v1'
_OURA_API_V2 = 'https://api.ouraring.com/v2'


class OuraEndpoints(enum.Enum):
  """Represents Oura endpoints."""
  ACTIVITY = '{}/usercollection/daily_activity'.format(_OURA_API_V2)
  BEDTIME = '{}/bedtime'.format(_OURA_API_V1)
  HEART_RATE = '{}/usercollection/heartrate'.format(_OURA_API_V2)
  READINESS = '{}/usercollection/daily_readiness'.format(_OURA_API_V2)
  SESSIONS = '{}/usercollection/session'.format(_OURA_API_V2)
  SLEEP_PERIODS = '{}/usercollection/sleep'.format(_OURA_API_V2)
  SLEEP_SCORE = '{}/usercollection/daily_sleep'.format(_OURA_API_V2)
  WORKOUTS = '{}/usercollection/workout'.format(_OURA_API_V2)


class OuraApi(object):
  """Handles Oura API interactions.

  Properties:
    token_file_name: Name of the file that contains the sensor credentials.

  Methods:
    get_oura_data: fetches data from Oura API for given endpoint.
  """

  def __init__(self, sensor, access_token):
    """Instantiates a new OuraApi class.

    Args:
      sensor: Oura sensor to which this api is linked.
      access_token: Personal access token.
    """
    self._sensor = sensor
    self._access_token = access_token
    self._hass_url = hass_helper.get_url(self._sensor._hass)

  def _get_oura_data_legacy(self, endpoint, start_date, end_date=None):
    """Fetches data for a OuraEndpoint and date for API v1.

    Args:
      start_date: Day for which to fetch data(YYYY-MM-DD).
      end_date: Last day for which to retrieve data(YYYY-MM-DD).
        If same as start_date, leave empty.

    Returns:
      Dictionary containing Oura sleep data.
    """
    api_url = endpoint.value

    params = {
        'access_token': self._access_token,
    }
    if start_date:
      params['start'] = start_date
    if end_date:
      params['end'] = end_date

    response = requests.get(api_url, params=params)
    response_data = response.json()

    return response_data

  def get_oura_data(self, endpoint, start_date, end_date=None):
    """Fetches data for a OuraEndpoint and date.

    TODO: detect whether data was retrieved.
    TODO: detect whether next_token is present. If yes, fetch and combine.

    Args:
      start_date: Day for which to fetch data(YYYY-MM-DD).
      end_date: Last day for which to retrieve data(YYYY-MM-DD).
        If same as start_date, leave empty.

    Returns:
      Dictionary containing Oura sleep data.
    """
    api_url = endpoint.value

    if _OURA_API_V1 in api_url:
      return self._get_oura_data_legacy(endpoint, start_date, end_date)

    params = {}
    if start_date:
      params['start_date'] = start_date
    if end_date:
      params['end_date'] = end_date

    headers = {
        'Authorization': 'Bearer {}'.format(self._access_token)
    }

    response = requests.get(api_url, params=params, headers=headers)
    response_data = response.json()

    return response_data
