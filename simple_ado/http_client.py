#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO HTTP API wrapper."""

import datetime
import logging
import os
import time
from typing import Any, cast

import requests
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from simple_ado.auth.ado_auth import ADOAuth
from simple_ado.exceptions import ADOException, ADOHTTPException
from simple_ado.models import PatchOperation


# pylint: disable=invalid-name
ADOThread = dict[str, Any]
ADOResponse = Any
# pylint: enable=invalid-name


def _is_retryable_get_failure(exception: Exception) -> bool:
    if not isinstance(exception, ADOHTTPException):
        return False

    return cast(ADOHTTPException, exception).response.status_code in range(400, 500)


def _is_connection_failure(exception: Exception) -> bool:
    exception_checks = [
        "Operation timed out",
        "Connection aborted.",
        "bad handshake: ",
        "Failed to establish a new connection",
    ]

    for check in exception_checks:
        if check in str(exception):
            return True

    return False


class ADOHTTPClient:
    """Base class that actually makes API calls to Azure DevOps.

    :param tenant: The name of the ADO tenant to connect to
    :param extra_headers: Any extra headers which should be added to each request
    :param user_agent: The user agent to set
    :param auth: The authentication details
    :param log: The logger to use for logging
    """

    log: logging.Logger
    tenant: str
    extra_headers: dict[str, str]
    auth: ADOAuth
    _not_before: datetime.datetime | None
    _session: requests.Session

    def __init__(
        self,
        *,
        tenant: str,
        auth: ADOAuth,
        user_agent: str,
        log: logging.Logger,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        """Construct a new client object."""

        self.log = log.getChild("http")

        self.tenant = tenant
        self.auth = auth
        self._not_before = None

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": f"simple_ado/{user_agent}"})

        if extra_headers is None:
            self.extra_headers = {}
        else:
            self.extra_headers = extra_headers

    def graph_endpoint(self) -> str:
        """Generate the base url for all graph API calls (this varies depending on the API).

        :returns: The constructed graph URL
        """
        return f"https://vssps.dev.azure.com/{self.tenant}/_apis"

    def audit_endpoint(self) -> str:
        """Generate the base url for all audit API calls.

        :returns: The constructed graph URL
        """
        return f"https://auditservice.dev.azure.com/{self.tenant}/_apis"

    def api_endpoint(
        self,
        *,
        is_default_collection: bool = True,
        is_internal: bool = False,
        subdomain: str | None = None,
        project_id: str | None = None,
    ) -> str:
        """Generate the base url for all API calls (this varies depending on the API).

        :param is_default_collection: Whether this URL should start with the path "/DefaultCollection"
        :param is_internal: Whether this URL should use internal API endpoint "/_api"
        :param subdomain: A subdomain that should be used (if any)
        :param project_id: The project ID. This will be added if supplied

        :returns: The constructed base URL
        """

        url = f"https://{self.tenant}."

        if subdomain:
            url += subdomain + "."

        url += "visualstudio.com"

        if is_default_collection:
            url += "/DefaultCollection"

        if project_id:
            url += f"/{project_id}"

        if is_internal:
            url += "/_api"
        else:
            url += "/_apis"

        return url

    def _wait(self):
        """Wait as long as we need for rate limiting purposes."""
        if not self._not_before:
            return

        remaining = self._not_before - datetime.datetime.now()

        if remaining.total_seconds() < 0:
            self._not_before = None
            return

        self.log.debug(f"Sleeping for {remaining} seconds before issuing next request")
        time.sleep(remaining.total_seconds())

    def _track_rate_limit(self, response: requests.Response) -> None:
        """Track the rate limit info from a request.

        :param response: The response to track the info from.
        """

        if "Retry-After" in response.headers:
            # We get massive windows for retry after, so we wait 10 seconds or
            # the duration, whichever is smaller. If we get a 429, we'll increase.
            self._not_before = datetime.datetime.now() + datetime.timedelta(
                seconds=min(15, int(response.headers["Retry-After"]))
            )
            return

        # Slow down if needed
        if int(response.headers.get("X-RateLimit-Remaining", 100)) < 10:
            self._not_before = datetime.datetime.now() + datetime.timedelta(seconds=1)
            return

        # No limit, so go at full speed
        self._not_before = None

    @retry(
        retry=(
            retry_if_exception(_is_connection_failure)  # type: ignore
            | retry_if_exception(_is_retryable_get_failure)  # type: ignore
        ),
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
    def get(
        self,
        request_url: str,
        *,
        additional_headers: dict[str, str] | None = None,
        stream: bool = False,
        allow_redirects: bool = True,
        set_accept_json: bool = True,
    ) -> requests.Response:
        """Issue a GET request with the correct headers.

        :param request_url: The URL to issue the request to
        :param additional_headers: Any additional headers to add to the request
        :param stream: Set to True to stream the response back
        :param allow_redirects: Set to False to disable redirects
        :param set_accept_json: Set to False to disable setting the Accept header

        :returns: The raw response object from the API
        """
        self._wait()

        headers = self.construct_headers(
            additional_headers=additional_headers, set_accept_json=False
        )

        response = self._session.get(
            request_url,
            headers=headers,
            stream=stream,
            allow_redirects=allow_redirects,
        )

        self._track_rate_limit(response)

        return response

    @retry(
        retry=retry_if_exception(_is_connection_failure),  # type: ignore
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
    def post(
        self,
        request_url: str,
        *,
        operations: list[PatchOperation] | None = None,
        additional_headers: dict[str, str] | None = None,
        json_data: Any | None = None,
        stream: bool = False,
    ) -> requests.Response:
        """Issue a POST request with the correct  headers.

        Note: If `json_data` and `operations` are not None, the latter will take
        precedence.

        :param request_url: The URL to issue the request to
        :param operations: The patch operations to send with the request
        :param additional_headers: Any additional headers to add to the request
        :param json_data: The JSON data to send with the request
        :param stream: Set to True to stream the response back

        :returns: The raw response object from the API
        """

        if operations is not None:
            json_data = [operation.serialize() for operation in operations]
            if additional_headers is None:
                additional_headers = {}
            if "Content-Type" not in additional_headers:
                additional_headers["Content-Type"] = "application/json-patch+json"

        headers = self.construct_headers(additional_headers=additional_headers)
        return self._session.post(
            request_url,
            headers=headers,
            json=json_data,
            stream=stream,
        )

    @retry(
        retry=retry_if_exception(_is_connection_failure),  # type: ignore
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
    def patch(
        self,
        request_url: str,
        *,
        operations: list[PatchOperation] | None = None,
        json_data: Any | None = None,
        additional_headers: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Issue a PATCH request with the correct headers.

        Note: If `json_data` and `operations` are not None, the latter will take
        precedence.

        :param request_url: The URL to issue the request to
        :param additional_headers: Any additional headers to add to the request
        :param json_data: The JSON data to send with the request
        :param operations: The patch operations to send with the request

        :returns: The raw response object from the API
        """

        if operations is not None:
            json_data = [operation.serialize() for operation in operations]
            if additional_headers is None:
                additional_headers = {}
            if "Content-Type" not in additional_headers:
                additional_headers["Content-Type"] = "application/json-patch+json"

        headers = self.construct_headers(additional_headers=additional_headers)
        return self._session.patch(request_url, headers=headers, json=json_data)

    @retry(
        retry=retry_if_exception(_is_connection_failure),  # type: ignore
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
    def put(
        self,
        request_url: str,
        json_data: Any | None = None,
        *,
        additional_headers: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Issue a PUT request with the correct headers.

        :param request_url: The URL to issue the request to
        :param additional_headers: Any additional headers to add to the request
        :param json_data: The JSON data to send with the request

        :returns: The raw response object from the API
        """
        headers = self.construct_headers(additional_headers=additional_headers)
        return self._session.put(request_url, headers=headers, json=json_data)

    @retry(
        retry=retry_if_exception(_is_connection_failure),  # type: ignore
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
    def delete(
        self, request_url: str, *, additional_headers: dict[str, Any] | None = None
    ) -> requests.Response:
        """Issue a DELETE request with the correct headers.

        :param request_url: The URL to issue the request to
        :param additional_headers: Any additional headers to add to the request

        :returns: The raw response object from the API
        """
        headers = self.construct_headers(additional_headers=additional_headers)
        return self._session.delete(request_url, headers=headers)

    @retry(
        retry=retry_if_exception(_is_connection_failure),  # type: ignore
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
    def post_file(
        self,
        request_url: str,
        file_path: str,
        *,
        additional_headers: dict[str, Any] | None = None,
    ) -> requests.Response:
        """POST a file to the URL with the given file name.

        :param request_url: The URL to issue the request to
        :param file_path: The path to the file to be posted
        :param additional_headers: Any additional headers to add to the request

        :returns: The raw response object from the API"""

        file_size = os.path.getsize(file_path)

        headers = self.construct_headers(additional_headers=additional_headers)
        headers["Content-Length"] = str(file_size)
        headers["Content-Type"] = "application/json"

        request = requests.Request("POST", request_url, headers=headers)
        prepped = request.prepare()

        # Send the raw content, not with "Content-Disposition", etc.
        with open(file_path, "rb") as file_handle:
            prepped.body = file_handle.read(file_size)

        response: requests.Response = self._session.send(prepped)
        return response

    def validate_response(self, response: requests.models.Response) -> None:
        """Checking a response for errors.

        :param response: The response to check

        :raises ADOHTTPException: Raised if the request returned a non-200 status code
        :raises ADOException: Raise if the response was not JSON
        """

        self.log.debug("Validating response from ADO")

        if response.status_code < 200 or response.status_code >= 300:
            raise ADOHTTPException(
                f"ADO returned a non-200 status code, configuration={self}",
                response,
            )

    def decode_response(self, response: requests.models.Response) -> ADOResponse:
        """Decode the response from ADO, checking for errors.

        :param response: The response to check and parse

        :returns: The JSON data from the ADO response

        :raises ADOHTTPException: Raised if the request returned a non-200 status code
        :raises ADOException: Raise if the response was not JSON
        """

        self.validate_response(response)

        self.log.debug("Decoding response from ADO")

        try:
            content: ADOResponse = response.json()
        except Exception as ex:
            raise ADOException("The response did not contain JSON") from ex

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
        except Exception as ex:
            raise ADOException(
                "The response was invalid (did not contain a value)."
            ) from ex

    def construct_headers(
        self,
        *,
        additional_headers: dict[str, str] | None = None,
        set_accept_json: bool = True,
    ) -> dict[str, str]:
        """Contruct the headers used for a request, adding anything additional.

        :param additional_headers: A dictionary of the additional headers to add.
        :param set_accept_json: Set to False to disable setting the Accept header

        :returns: A dictionary of the headers for a request
        """

        headers = {}

        if set_accept_json:
            headers["Accept"] = "application/json"

        headers["Authorization"] = self.auth.get_authorization_header()

        for header_name, header_value in self.extra_headers.items():
            headers[header_name] = header_value

        if additional_headers is None:
            return headers

        for header_name, header_value in additional_headers.items():
            headers[header_name] = header_value

        return headers
