"""Provides a base OuraSensor class to handle interactions with Oura API."""

from homeassistant import const
from homeassistant.helpers import entity
from . import api
from . import views

_CONF_CLIENT_ID = 'client_id'
_CONF_CLIENT_SECRET = 'client_secret'
_CONF_BACKFILL = 'max_backfill'

# Sensor config.
SENSOR = 'oura'
SENSOR_NAME = 'Oura Ring'


class OuraSensor(entity.Entity):
  """Representation of an Oura Ring sensor.

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

    self._config = config
    self._hass = hass

    # Basic sensor config.
    self._name = config.get(const.CONF_NAME)
    self._sensor_name = SENSOR_NAME
    self._backfill = config.get(_CONF_BACKFILL)

    # API config.
    client_id = self._config.get(_CONF_CLIENT_ID)
    client_secret = self._config.get(_CONF_CLIENT_SECRET)
    self._api = api.OuraApi(self, client_id, client_secret)

    # Attributes.
    self._state = None  # Sleep score.
    self._attributes = {}

  # Oura set up logic.
  def create_oauth_view(self, authorize_url):
    """Creates a view and message to obtain authorization token.

    Args:
      authorize_url: Authorization URL.
    """
    self._hass.http.register_view(views.OuraAuthCallbackView(self))
    self._hass.components.persistent_notification.create(
        'In order to authorize Home-Assistant to view your Oura Ring data, '
        'you must visit: '
        f'<a href="{authorize_url}" target="_blank">{authorize_url}</a>. Make '
        f'sure that you have added {self._api.get_auth_url()} to your '
        'Redirect URIs on Oura Cloud Developer application.',
        title=self._sensor_name,
        notification_id=f'oura_setup_{self._name}')

  # Sensor properties.
  @property
  def name(self):
    """Returns the name of the sensor."""
    return self._name

  @property
  def state(self):
    """Returns the state of the sensor."""
    return self._state

  @property
  def extra_state_attributes(self):
    """Returns the sensor attributes."""
    return self._attributes

  # Sensor methods.
  def _update(self):
    """To be implemented by the sensor."""

  async def async_update(self):
    """Updates the state and attributes of the sensor."""
    await self._hass.async_add_executor_job(self._update)
