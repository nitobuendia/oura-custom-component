"""ensor from Oura Ring data."""

from homeassistant import const
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from . import sensor_sleep

_DEFAULT_SENSORS_SCHEMA = {
    const.CONF_SENSORS: sensor_sleep.DEFAULT_CONFIG,
}

_SENSORS_SCHEMA = {
    vol.Optional(sensor_sleep.CONF_KEY_NAME): sensor_sleep.CONF_SCHEMA,
}

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend({
    vol.Required(const.CONF_ACCESS_TOKEN): cv.string,

    vol.Optional(
        const.CONF_SENSORS,
        default=_DEFAULT_SENSORS_SCHEMA
    ): _SENSORS_SCHEMA,
})


async def setup(hass, config):
  """No set up required. Token retrieval logic handled by sensor."""
  return True


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
  """Adds sensor platform to the list of platforms."""
  sensors_config = config.get(const.CONF_SENSORS, {})
  sensors = []

  if sensor_sleep.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_sleep.OuraSleepSensor(config, hass))

  async_add_entities(sensors, True)
