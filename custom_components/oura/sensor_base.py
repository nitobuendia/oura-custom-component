"""Provides a base OuraSensor class to handle interactions with Oura API."""

import logging
from homeassistant import const
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity
from . import api

SENSOR_NAME = 'oura'


class OuraSensor(entity.Entity):
  """Representation of an Oura Ring sensor.

  Attributes:
    name: name of the sensor.
    state: state of the sensor.
    extra_state_attributes: attributes of the sensor.

  Methods:
    async_update: updates sensor data.
  """

  def __init__(self, config, hass):
    """Initializes the sensor."""

    # Basic sensor config.
    self._config = config
    self._sensor_config = {}
    self._hass = hass
    self._name = SENSOR_NAME

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
