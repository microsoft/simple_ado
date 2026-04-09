#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO exceptions."""

import httpx


class ADOException(Exception):
    """All ADO exceptions inherit from this or instantiate it."""


class _CompatResponse:
    """Thin wrapper around httpx.Response that adds backward-compatible .ok property.

    The requests library provided response.ok (status_code < 400). httpx uses
    response.is_success (200 <= status_code < 300) instead. This wrapper adds .ok
    so that code written against the old requests-based API still works.

    All other attribute access is delegated to the underlying httpx.Response.
    """

    _response: httpx.Response

    def __init__(self, response: httpx.Response) -> None:
        # Use object.__setattr__ to avoid triggering __setattr__ if overridden
        object.__setattr__(self, "_response", response)

    @property
    def ok(self) -> bool:
        """Backward-compatible alias: True when status_code < 400."""
        return self._response.status_code < 400

    def __getattr__(self, name: str) -> object:
        return getattr(self._response, name)

    def __repr__(self) -> str:
        return repr(self._response)


class ADOHTTPException(ADOException):
    """All ADO HTTP exceptions use this class.

    :param message: The message for the exception
    :param response: The response to the HTTP request
    """

    message: str
    response: _CompatResponse

    def __init__(self, message: str, response: httpx.Response) -> None:
        super().__init__()
        self.message = message
        self.response = _CompatResponse(response)

    def __str__(self) -> str:
        """Generate and return the string representation of the object.

        :return: A string representation of the object
        """
        return f"{self.message}, status_code={self.response.status_code}, text={self.response.text}"
