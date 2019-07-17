#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO HTTP API wrapper."""

import logging
import os
import time
from typing import Any, Callable, Dict, Optional, Tuple

import requests

from simple_ado.exceptions import ADOException, ADOHTTPException


# pylint: disable=invalid-name
ADOThread = Dict[str, Any]
ADOResponse = Any
# pylint: enable=invalid-name


def exception_retry(
    max_attempts: int = 3,
    initial_delay: float = 5,
    backoff_factor: int = 2,
    should_retry: Optional[Callable[[Exception], bool]] = None,
) -> Callable:
    """Retry an API call at many times as required with a backoff factor.

    :param max_attempts: The maximum number of times we should attempt to retry
    :param initial_delay: How long we should wait after the first failure
    :param backoff_factor: What factor should we increase the delay by for each failure
    :param should_retry: A function which will be called with the exception to determine if we should retry or not

    :returns: A wrapped function

    :raises ValueError: If any of the inputs are invalid
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be 1 or more")

    if initial_delay < 0:
        raise ValueError("initial_delay must be a positive (or 0) float")

    if backoff_factor < 1:
        raise ValueError("backoff_factor must be a postive integer greater than or equal to 1")

    def decorator(function: Callable) -> Callable:
        """Decorator function

        :param function: The function to wrap

        :returns: The wrapped function
        """

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """The wrapper around the function.

            :param args: The unnamed arguments to the function
            :param kwargs: The named arguments to the function

            :returns: Whatever value the original function returns on success

            :raises ADOHTTPException: Any exception that the wrapped function raises
            :raises Exception: Any exception that the wrapped function raises
            """

            # Check for a log argument to the function first
            log = kwargs.get("log")

            if log is not None:
                log = log.getChild("retry")

            # If we still don't have one, check if the function is on an object
            # and use the log variable from that if possible
            if log is None:
                try:
                    # This works around a mypy issue
                    any_self: Any = args[0]
                    log = any_self.log
                except AttributeError:
                    pass

            # If we still have nothing, create a new logger
            if log is None:
                log = logging.getLogger("ado.retry")

            remaining_attempts = max_attempts
            current_delay = initial_delay

            while remaining_attempts > 1:
                exception_reference: Optional[Exception] = None

                try:
                    return function(*args, **kwargs)

                except ADOHTTPException as ex:
                    # We can't retry non-server errors
                    if ex.response.status_code < 500:
                        raise

                    if should_retry is not None and not should_retry(ex):
                        log.error("ADO API call failed. Not retrying.")
                        raise

                    exception_reference = ex

                except Exception as ex:
                    if should_retry is not None and not should_retry(ex):
                        log.error(f"ADO API call failed. Not retrying.")
                        raise

                    exception_reference = ex

                    time.sleep(current_delay)
                    remaining_attempts -= 1
                    current_delay *= backoff_factor

                log.warning(
                    f"ADO API call failed. Retrying in {current_delay} seconds: {exception_reference}"
                )

            return function(*args, **kwargs)

        return wrapper

    return decorator


class ADOHTTPClient:
    """Base class that actually makes API calls to Azure DevOps.

    :param str tenant: The name of the ADO tenant to connect to
    :param str project_id: The ID of the ADO project to connect to
    :param Dict[str,str] extra_headers: Any extra headers which should be added to each request
    :param Tuple[str,str] credentials: The credentials which should be used for authentication
    :param logging.Logger log: The logger to use for logging
    """

    log: logging.Logger
    tenant: str
    project_id: str
    extra_headers: Dict[str, str]
    credentials: Tuple[str, str]

    def __init__(
        self,
        *,
        tenant: str,
        project_id: str,
        credentials: Tuple[str, str],
        log: logging.Logger,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Construct a new client object."""

        self.log = log.getChild("http")

        self.tenant = tenant
        self.project_id = project_id
        self.credentials = credentials

        if extra_headers is None:
            self.extra_headers = {}
        else:
            self.extra_headers = extra_headers

    def base_url(
        self,
        *,
        is_default_collection: bool = True,
        is_project: bool = True,
        is_internal: bool = False,
    ) -> str:
        """Generate the base url for all API calls (this varies depending on the API).

        :param bool is_default_collection: Whether this URL should start with the path "/DefaultCollection"
        :param bool is_project: Whether this URL should scope down to include `project_id`
        :param bool is_internal: Whether this URL should use internal API endpoint "/_api"

        :returns: The constructed base URL
        """

        url = f"https://{self.tenant}.visualstudio.com"

        if is_default_collection:
            url += "/DefaultCollection"

        if is_project:
            url += f"/{self.project_id}"

        if is_internal:
            url += "/_api"
        else:
            url += "/_apis"

        return url

    @exception_retry(
        should_retry=lambda exception: isinstance(exception, ADOHTTPException)
        and exception.response.status_code not in range(400, 500)
    )
    def get(
        self, request_url: str, *, additional_headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """Issue a GET request with the correct credentials and headers.

        :param str request_url: The URL to issue the request to
        :param Optional[Dict[str,str]] additional_headers: Any additional headers to add to the request

        :returns: The raw response object from the API
        """
        headers = self.construct_headers(additional_headers=additional_headers)
        return requests.get(request_url, auth=self.credentials, headers=headers)

    @exception_retry(
        should_retry=lambda exception: "Operation timed out" in str(exception)
        or "Connection aborted." in str(exception)
        or "bad handshake: " in str(exception)
    )
    def post(
        self,
        request_url: str,
        *,
        additional_headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Issue a POST request with the correct credentials and headers.

        :param str request_url: The URL to issue the request to
        :param Optional[Dict[str,str]] additional_headers: Any additional headers to add to the request
        :param Optional[Dict[str,Any]] json_data: The JSON data to send with the request

        :returns: The raw response object from the API
        """
        headers = self.construct_headers(additional_headers=additional_headers)
        return requests.post(request_url, auth=self.credentials, headers=headers, json=json_data)

    def patch(
        self,
        request_url: str,
        json_data: Optional[Any] = None,
        *,
        additional_headers: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Issue a PATCH request with the correct credentials and headers.

        :param str request_url: The URL to issue the request to
        :param Optional[Dict[str,str]] additional_headers: Any additional headers to add to the request
        :param Optional[Dict[str,Any]] json_data: The JSON data to send with the request

        :returns: The raw response object from the API
        """
        headers = self.construct_headers(additional_headers=additional_headers)
        return requests.patch(request_url, auth=self.credentials, headers=headers, json=json_data)

    def delete(
        self, request_url: str, *, additional_headers: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Issue a DELETE request with the correct credentials and headers.

        :param str request_url: The URL to issue the request to
        :param Optional[Dict[str,str]] additional_headers: Any additional headers to add to the request

        :returns: The raw response object from the API
        """
        headers = self.construct_headers(additional_headers=additional_headers)
        return requests.delete(request_url, auth=self.credentials, headers=headers)

    def post_file(
        self,
        request_url: str,
        file_path: str,
        *,
        additional_headers: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """POST a file to the URL with the given file name.

        :param str request_url: The URL to issue the request to
        :param str file_path: The path to the file to be posted
        :param Optional[Dict[str,str]] additional_headers: Any additional headers to add to the request

        :returns: The raw response object from the API"""

        file_size = os.path.getsize(file_path)

        headers = self.construct_headers(additional_headers=additional_headers)
        headers["Content-Length"] = str(file_size)
        headers["Content-Type"] = "application/json"

        request = requests.Request("POST", request_url, headers=headers, auth=self.credentials)
        prepped = request.prepare()

        # Send the raw content, not with "Content-Disposition", etc.
        with open(file_path, "rb") as file_handle:
            prepped.body = file_handle.read(file_size)

        session = requests.Session()
        response: requests.Response = session.send(prepped)
        return response

    def decode_response(self, response: requests.models.Response) -> ADOResponse:
        """Decode the response from ADO, checking for errors.

        :param response: The response to check and parse

        :returns: The JSON data from the ADO response

        :raises ADOHTTPException: Raised if the request returned a non-200 status code
        :raises ADOException: Raise if the response was not JSON
        """

        self.log.debug("Fetching response from ADO")

        if response.status_code < 200 or response.status_code >= 300:
            raise ADOHTTPException(
                f"ADO returned a non-200 status code, configuration={self}",
                response,
            )

        try:
            content: ADOResponse = response.json()
        except:
            raise ADOException("The response did not contain JSON")

        return content

    def extract_value(self, response_data: ADOResponse) -> ADOResponse:
        """Extract the "value" from the raw JSON data from an API response

        :param response_data: The raw JSON data from an API response

        :returns: The ADO response with the data in it

        :raises ADOException: If the response is invalid (does not support value extraction)
        """

        self.log.debug("Extracting value")

        try:
            value: ADOResponse = response_data["value"]
            return value
        except:
            raise ADOException("The response was invalid (did not contain a value).")

    def construct_headers(
        self, *, additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Contruct the headers used for a request, adding anything additional.

        :param Optional[Dict[str,str]] additional_headers: A dictionary of the additional headers to add.

        :returns: A dictionary of the headers for a request
        """

        headers = {"Accept": "application/json"}

        for header_name, header_value in self.extra_headers:
            headers[header_name] = header_value

        if additional_headers is None:
            return headers

        for header_name, header_value in additional_headers:
            headers[header_name] = header_value

        return headers
