"""ensor from Oura Ring data."""

from homeassistant import const
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from . import sensor_activity
from . import sensor_base
from . import sensor_bedtime
from . import sensor_readiness
from . import sensor_sleep

_DEFAULT_SENSORS_SCHEMA = {
    const.CONF_SENSORS: sensor_sleep.DEFAULT_CONFIG,
}

_SENSORS_SCHEMA = {
    vol.Optional(
        sensor_base.CONF_KEY_NAME,
        default=sensor_base.DEFAULT_CONFIG
    ): sensor_base.CONF_SCHEMA,

    vol.Optional(
        sensor_activity.CONF_KEY_NAME,
        default=sensor_activity.DEFAULT_CONFIG
    ): sensor_activity.CONF_SCHEMA,

    vol.Optional(
        sensor_bedtime.CONF_KEY_NAME,
        default=sensor_bedtime.DEFAULT_CONFIG
    ): sensor_bedtime.CONF_SCHEMA,

    vol.Optional(
        sensor_readiness.CONF_KEY_NAME,
        default=sensor_readiness.DEFAULT_CONFIG
    ): sensor_readiness.CONF_SCHEMA,

    vol.Optional(
        sensor_sleep.CONF_KEY_NAME,
        default=sensor_sleep.DEFAULT_CONFIG
    ): sensor_sleep.CONF_SCHEMA,
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

  if sensor_activity.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_activity.OuraActivitySensor(config, hass))

  if sensor_bedtime.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_bedtime.OuraBedtimeSensor(config, hass))

  if sensor_readiness.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_readiness.OuraReadinessSensor(config, hass))

  if sensor_sleep.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_sleep.OuraSleepSensor(config, hass))

  async_add_entities(sensors, True)
