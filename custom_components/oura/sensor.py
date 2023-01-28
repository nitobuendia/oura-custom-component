"""Sensor from Oura Ring data."""

from homeassistant import const
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from . import sensor_activity
from . import sensor_bedtime
from . import sensor_heart_rate
from . import sensor_readiness
from . import sensor_sessions
from . import sensor_sleep
from . import sensor_sleep_periods
from . import sensor_sleep_score
from . import sensor_workouts


_SENSORS_SCHEMA = {
    vol.Optional(sensor_activity.CONF_KEY_NAME): sensor_activity.CONF_SCHEMA,
    vol.Optional(sensor_bedtime.CONF_KEY_NAME): sensor_bedtime.CONF_SCHEMA,
    vol.Optional(
        sensor_heart_rate.CONF_KEY_NAME): sensor_heart_rate.CONF_SCHEMA,
    vol.Optional(sensor_readiness.CONF_KEY_NAME): sensor_readiness.CONF_SCHEMA,
    vol.Optional(sensor_sessions.CONF_KEY_NAME): sensor_sessions.CONF_SCHEMA,
    vol.Optional(sensor_sleep.CONF_KEY_NAME): sensor_sleep.CONF_SCHEMA,
    vol.Optional(
        sensor_sleep_periods.CONF_KEY_NAME): sensor_sleep_periods.CONF_SCHEMA,
    vol.Optional(
        sensor_sleep_score.CONF_KEY_NAME): sensor_sleep_score.CONF_SCHEMA,
    vol.Optional(sensor_workouts.CONF_KEY_NAME): sensor_workouts.CONF_SCHEMA,
}

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend({
    vol.Required(const.CONF_ACCESS_TOKEN): cv.string,
    vol.Optional(const.CONF_SENSORS): _SENSORS_SCHEMA,
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

  if sensor_heart_rate.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_heart_rate.OuraHeartRateSensor(config, hass))

  if sensor_readiness.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_readiness.OuraReadinessSensor(config, hass))

  if sensor_sessions.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_sessions.OuraSessionsSensor(config, hass))

  if sensor_sleep.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_sleep.OuraSleepSensor(config, hass))

  if sensor_sleep_periods.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_sleep_periods.OuraSleepPeriodsSensor(config, hass))

  if sensor_sleep_score.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_sleep_score.OuraSleepScoreSensor(config, hass))

  if sensor_workouts.CONF_KEY_NAME in sensors_config:
    sensors.append(sensor_workouts.OuraWorkoutsSensor(config, hass))

  async_add_entities(sensors, True)
