"""Provides an OuraApi class to handle interactions with Oura API."""

import enum
import json
import logging
import os
import requests
import urllib
from . import views

# Oura API config.
_TOKEN_FILE = 'oura-token-cache-{}'
_OURA_API = 'https://api.ouraring.com/v1'
_OURA_CLOUD = 'https://cloud.ouraring.com'
_MAX_API_RETRIES = 3


class OuraEndpoints(enum.Enum):
  """Represents Oura endpoints."""
  # Data endpoints.
  ACTIVITY = '{}/activity'.format(_OURA_API)
  READINESS = '{}/readiness'.format(_OURA_API)
  SLEEP = '{}/sleep'.format(_OURA_API)
  USER_INFO = '{}/userinfo'.format(_OURA_API)
  # Auth endpoints.
  AUTHORIZE = '{}/oauth/authorize'.format(_OURA_CLOUD)
  TOKEN = '{}/oauth/token'.format(_OURA_CLOUD)


class OuraApi(object):
  """Handles Oura API interactions.

  Properties:
    token_file_name: Name of the file that contains the sensor credentials.

  Methods:
    get_sleep_data: fetches sleep data from Oura cloud data.
  """

  def __init__(self, sensor, client_id, client_secret):
    """Instantiates a new OuraApi class.

    Args:
      sensor: Oura sensor to which this api is linked.
      client_id: Client id for Oura API.
      client_secret: Client secret for Oura API.
    """
    self._sensor = sensor

    self._client_id = client_id
    self._client_secret = client_secret

    self._access_token = None
    self._refresh_token = None

  def get_sleep_data(self, start_date, end_date=None):
    """Fetches data for a sleep OuraEndpoint and date.

    Args:
      start_date: Day for which to fetch data(YYYY-MM-DD).
      end_date: Last day for which to retrieve data(YYYY-MM-DD).
        If same as start_date, leave empty.

    Returns:
      Dictionary containing Oura sleep data.
      None if the access token was not found or authorized.
    """
    if not self._access_token:
      self._get_access_token_data_from_file()

    # If after fetching the token, it is still not available, the update should
    # not go through. This is most likely at the OAuth set up stage and may
    # require input from the user.
    if not self._access_token:
      return None

    retries = 0
    while retries < _MAX_API_RETRIES:
      api_url = self._get_api_endpoint(OuraEndpoints.SLEEP,
                                       start_date=start_date)

      response = requests.get(api_url)
      response_data = response.json()

      if not response_data:
        retries += 1
        continue

      if response_data.get('message') == 'Unauthorized':
        retries += 1
        self._refresh_access_token()
        continue

      return response_data

    logging.error(
        'Couldn\'t fetch data for Oura ring sensor. Verify API token.')
    return None


  def _get_api_endpoint(self, api_endpoint, **kwargs):
    """Gets URL for a given endpoint and day.

    Args:
      api_endpoint: Endpoint(OuraEndpoints) from which to fetch data.

    Optional Keyword Args:
      start_date: Day for which to fetch data(YYYY-MM-DD).
        > Required for SLEEP endpoint.
      end_date: Day to which to fetch data(YYYY-MM-DD).
        > Optional, used for SLEEP endpoint.

    Returns:
      Full Oura API endpoint URL.
    """
    if api_endpoint == OuraEndpoints.SLEEP:
      sleep_api_url = '{oura_url}?access_token={access_token}'.format(
          oura_url=api_endpoint.value,
          access_token=self._access_token,
      )

      if kwargs.get('start_date'):
        sleep_api_url = (
            sleep_api_url + '&start={}'.format(kwargs['start_date']))

      if kwargs.get('end_date'):
        sleep_api_url = sleep_api_url + '&end={}'.format(kwargs['end_date'])

      return sleep_api_url

    elif api_endpoint in [OuraEndpoints.TOKEN, OuraEndpoints.AUTHORIZE]:
      return api_endpoint.value

    else:
      return '{oura_url}?access_token={access_token}'.format(
          oura_url=api_endpoint.value,
          access_token=self._access_token,
      )

  # Oura authentication.

  def _get_access_token_data_from_file(self):
    """Gets credentials data from the credentials file."""
    if not os.path.isfile(self.token_file_name):
      self._get_authentication_code()
      return

    with open(self.token_file_name, 'r') as token_file:
      token_data = json.loads(token_file.read()) or {}

    if token_data.get('code'):
      self._get_access_token_from_code(token_data.get('code'))
      return

    if token_data.get('access_token') and token_data.get('refresh_token'):
      self._access_token = token_data.get('access_token')
      self._refresh_token = token_data.get('refresh_token')

    logging.error('Unable to retrieve access token from file data.')

  def _get_authentication_code(self):
    """Gets authentication code."""
    base_url = self._sensor._hass.config.api.base_url
    callback_url = f'{base_url}{views.AUTH_CALLBACK_PATH}'

    authorize_params = {
        'client_id': self._client_id,
        'duration': 'temporary',
        'redirect_uri': callback_url,
        'response_type': 'code',
        'scope': 'email personal daily',
        'state': self._sensor.name,
    }
    authorize_url = '{}?{}'.format(
        self._get_api_endpoint(OuraEndpoints.AUTHORIZE),
        urllib.parse.urlencode(authorize_params))

    self._sensor.create_oauth_view(authorize_url)

  def _store_access_token_data(self, access_token_data):
    """Validates and stores access token data into file.

    Args:
      access_token_data: Dictionary containing access token and refresh token.
    """
    if 'access_token' not in access_token_data:
      logging.error('Oura API was unable to retrieve new API token.')
      return

    if 'refresh_token' not in access_token_data:
      if self._refresh_token:
        access_token_data['refresh_token'] = self._refresh_token
      else:
        logging.error(
            'Refresh token not available. Oura API will become unauthorized.')
        return

    self._access_token = access_token_data['access_token']
    self._refresh_token = access_token_data['refresh_token']

    with open(self.token_file_name, 'w+') as token_file:
      token_file.write(json.dumps(access_token_data))

  def _request_access_token_with_refresh_token(self):
    """Sends a request to get access token with the existing refresh token.

    Returns:
      Response from requesting new token.
      Most likely: Access and refresh token data in a dictionary.
    """
    request_auth = requests.auth.HTTPBasicAuth(self._client_id,
                                               self._client_secret)
    request_data = {
        'grant_type': 'refresh_token',
        'refresh_token': self._refresh_token,
    }
    request_url = self._get_api_endpoint(OuraEndpoints.TOKEN)

    response = requests.post(request_url, auth=request_auth, data=request_data)
    return response.json()

  def _request_access_token_with_code(self, code):
    """Sends a request to get access token with new OAuth code.

    Args:
      code: Oura code to fetch access token.

    Returns:
      Response from requesting new token.
      Most likely: Access and refresh token data in a dictionary.
    """
    request_auth = requests.auth.HTTPBasicAuth(self._client_id,
                                               self._client_secret)

    base_url = self._sensor._hass.config.api.base_url
    callback_url = f'{base_url}{views.AUTH_CALLBACK_PATH}'
    request_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': callback_url,
    }

    request_headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    }

    request_url = self._get_api_endpoint(OuraEndpoints.TOKEN)

    response = requests.post(
        request_url, auth=request_auth, data=request_data,
        headers=request_headers)

    return response.json()

  def _refresh_access_token(self):
    """Gets a new access token using refresh token."""
    access_token_data = self._request_access_token_with_refresh_token()
    self._store_access_token_data(access_token_data)

  def _get_access_token_from_code(self, code):
    """Requests and stores an access token for the given code.

    Args:
      code: Oura OAuth code.
    """
    access_token_data = self._request_access_token_with_code(code)
    self._store_access_token_data(access_token_data)

  # Oura API properties.
  @property
  def token_file_name(self):
    """Gets the API token file name for the related sensor."""
    return _TOKEN_FILE.format(self._sensor.name)
