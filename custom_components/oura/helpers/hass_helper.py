"""Abstracts hass logic away from Oura logic."""

import logging

# Safe importing as this module was not existing on previous versions
# of Home-Assistant.
try:
  from homeassistant.helpers import network
except ModuleNotFoundError:
  logging.debug('Network module not found.')


def get_url(hass):
  """Gets the required Home-Assistant URL for validation.

  Args:
    hass: Hass instance.

  Returns:
    Home-Assistant URL.
  """
  if network:
    try:
      return network.get_url(
          hass,
          allow_external=True,
          allow_internal=True,
          allow_ip=True,
          prefer_external=True,
          require_ssl=False)
    except AttributeError:
      logging.debug(
          'Hass version does not have get_url helper, using fall back.')

  base_url = hass.config.api.base_url
  if base_url:
    return base_url

  raise ValueError('Unable to obtain HASS url.')
