"""Sensors from Oura Ring data."""

from homeassistant import const
from homeassistant.helpers import config_validation
import voluptuous
from . import sensor_sleep

_CONF_BACKFILL = 'max_backfill'
_CONF_SUPPORTED_TYPES = ['sleep']

_DEFAULT_BACKFILL = 0
_DEFAULT_MONITORED_VARIABLES = ['yesterday']
_DEFAULT_NAME = 'sleep_score'
_DEFAULT_TYPE = 'sleep'  # Makes backward compatibility easier.

PLATFORM_SCHEMA = config_validation.PLATFORM_SCHEMA.extend({
    voluptuous.Required(const.CONF_CLIENT_ID): config_validation.string,
    voluptuous.Required(const.CONF_CLIENT_SECRET): config_validation.string,
    voluptuous.Optional(
        const.CONF_TYPE,
        default=_DEFAULT_TYPE): voluptuous.In(_CONF_SUPPORTED_TYPES),
    voluptuous.Optional(
        const.CONF_MONITORED_VARIABLES,
        default=_DEFAULT_MONITORED_VARIABLES): config_validation.ensure_list,
    voluptuous.Optional(
        const.CONF_NAME, default=_DEFAULT_NAME): config_validation.string,
    voluptuous.Optional(
        _CONF_BACKFILL,
        default=_DEFAULT_BACKFILL): config_validation.positive_int,
})


async def setup(hass, config):
  """No set up required. Token retrieval logic handled by sensor."""
  return True


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
  """Adds sensor platform to the list of platforms."""
  async_add_entities([sensor_sleep.OuraSleepSensor(config, hass)], True)
