"""Provides a base OuraSensor class to handle interactions with Oura API."""

from homeassistant import const
from homeassistant.helpers import entity
from . import api

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
    access_token = config.get(const.CONF_ACCESS_TOKEN)
    self._api = api.OuraApi(self, access_token)

    # Attributes.
    self._state = None  # Sleep score.
    self._attributes = {}

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
