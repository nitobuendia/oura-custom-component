"""Provides some basic date functionality to work with Oura dates."""

import datetime


def seconds_to_hours(time_in_seconds):
  """Parses times in seconds and converts it to hours."""
  return round(int(time_in_seconds) / (60 * 60), 2)


def add_days_to_string_date(string_date, days_to_add):
  """Adds (or subtracts) days from a string date.

  Args:
    string_date: Original date in YYYY-MM-DD.
    days_to_add: Number of days to add. Negative to subtract.

  Returns:
    Date in YYYY-MM-DD with days added.
  """
  date = datetime.datetime.strptime(string_date, '%Y-%m-%d')
  new_date = date + datetime.timedelta(days=days_to_add)
  return str(new_date.date())


def add_time_to_string_time(string_time, seconds_to_add):
  """Adds (or subtracts) seconds from an hour date.

  Args:
    string_time: Original time in HH:MM.
    seconds_to_add: Number of seconds to add. Negative to subtract.

  Returns:
    Time in HH:MM with seconds added.
  """
  time = datetime.datetime.strptime(string_time, '%H:%M')
  new_time = time + datetime.timedelta(seconds=seconds_to_add)
  return str(new_time.strftime('%H:%M'))
