"""Utilities for dealing with the ADO REST API."""


def boolstr(value: bool) -> str:
    """Return a boolean formatted as string for ADO calls

    :param value: The value to format

    :returns: A string representation of the boolean value
    """
    return str(value).lower()
