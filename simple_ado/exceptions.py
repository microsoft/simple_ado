#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO exceptions."""


class ADOException(Exception):
    """All ADO exceptions inherit from this or instantiate it."""


class ADOHTTPException(ADOException):
    """All ADO HTTP exceptions use this class.

    :param message: The message for the exception
    :param status_code: The HTTP status code causing this exception
    :param text: The text of the response causing this exception
    """

    message: str
    status_code: int
    text: str

    def __init__(self, message: str, status_code: int, text: str) -> None:
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.text = text

    def __str__(self) -> str:
        """Generate and return the string representation of the object.

        :return: A string representation of the object
        """
        return f"{self.message}, status_code={self.status_code}, text={self.text}"
