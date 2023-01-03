"""Provides basic math functionality."""


def safe_average(array):
  """Calculates the average of a list/array.

  Safe: If value is non numerical, it skips it.

  Args:
    array: List of values to add.

  Returns:
    Average of values of the array.
  """
  array_sum = 0
  array_length = 0

  for element in array:
    if type(element) == 'str' and element.isnumeric():
      element = float(element)

    if type(element) not in (int, float):
      continue

    array_sum += element
    array_length += 1

  if array_length == 0:
    return 0

  return array_sum / array_length
