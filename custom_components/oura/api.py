"""Provides an OuraApi class to handle interactions with Oura API."""

import enum
import logging
import os
import requests
from .helpers import hass_helper

# Oura API config.
_OURA_API_V2 = 'https://api.ouraring.com/v2'


class OuraEndpoints(enum.Enum):
  """Represents Oura endpoints."""
  SLEEP = '{}/usercollection/sleep'.format(_OURA_API_V2)
  SLEEP_SCORE = '{}/usercollection/daily_sleep'.format(_OURA_API_V2)


class OuraApi(object):
  """Handles Oura API interactions.

  Properties:
    token_file_name: Name of the file that contains the sensor credentials.

  Methods:
    get_sleep_data: fetches sleep data from Oura cloud data.
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

  def get_sleep_data(self, start_date, end_date=None):
    """Fetches data for a sleep OuraEndpoint and date.

    TODO: detect whether data was retrieved.
    TODO: detect whether next_token is present. If yes, fetch and combine.

    Args:
      start_date: Day for which to fetch data(YYYY-MM-DD).
      end_date: Last day for which to retrieve data(YYYY-MM-DD).
        If same as start_date, leave empty.

    Returns:
      Dictionary containing Oura sleep data.
      None if the access token was not found or authorized.
    """
    api_url = OuraEndpoints.SLEEP.value

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

  # Oura API properties.
  @property
  def token_file_name(self):
    """Gets the API token file name for the related sensor."""
    # From config/custom_components/oura to config/
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    token_file = _TOKEN_FILE.format(self._sensor.name)
    full_token_filepath = os.path.join(base_path, token_file)
    return full_token_filepath
