#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO HTTP API wrapper."""

import logging
import os
from typing import Any, cast, Dict, List, Optional, Tuple

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_random_exponential

from simple_ado.exceptions import ADOException, ADOHTTPException
from simple_ado.models import PatchOperation


# pylint: disable=invalid-name
ADOThread = Dict[str, Any]
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

    :param str tenant: The name of the ADO tenant to connect to
    :param Dict[str,str] extra_headers: Any extra headers which should be added to each request
    :param str user_agent: The user agent to set
    :param Tuple[str,str] credentials: The credentials which should be used for authentication
    :param logging.Logger log: The logger to use for logging
    """

    log: logging.Logger
    tenant: str
    extra_headers: Dict[str, str]
    credentials: Tuple[str, str]
    _session: requests.Session

    def __init__(
        self,
        *,
        tenant: str,
        credentials: Tuple[str, str],
        user_agent: str,
        log: logging.Logger,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Construct a new client object."""

        self.log = log.getChild("http")

        self.tenant = tenant
        self.credentials = credentials

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

    def api_endpoint(
        self,
        *,
        is_default_collection: bool = True,
        is_internal: bool = False,
        subdomain: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> str:
        """Generate the base url for all API calls (this varies depending on the API).

        :param bool is_default_collection: Whether this URL should start with the path "/DefaultCollection"
        :param bool is_internal: Whether this URL should use internal API endpoint "/_api"
        :param Optional[str] subdomain: A subdomain that should be used (if any)
        :param Optional[str] project_id: The project ID. This will be added if supplied

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

    @retry(
        retry=(
            retry_if_exception(_is_connection_failure)
            | retry_if_exception(_is_retryable_get_failure)
        ),
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
    def get(
        self,
        request_url: str,
        *,
        additional_headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
    ) -> requests.Response:
        """Issue a GET request with the correct credentials and headers.

        :param str request_url: The URL to issue the request to
        :param Optional[Dict[str,str]] additional_headers: Any additional headers to add to the request
        :param bool stream: Set to True to stream the response back

        :returns: The raw response object from the API
        """
        headers = self.construct_headers(additional_headers=additional_headers)
        return self._session.get(request_url, auth=self.credentials, headers=headers, stream=stream)

    @retry(
        retry=retry_if_exception(_is_connection_failure),
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
    def post(
        self,
        request_url: str,
        *,
        operations: Optional[List[PatchOperation]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Any] = None,
        stream: bool = False,
    ) -> requests.Response:
        """Issue a POST request with the correct credentials and headers.

        Note: If `json_data` and `operations` are not None, the latter will take
        precedence.

        :param str request_url: The URL to issue the request to
        :param Optional[List[PatchOperation]] operations: The patch operations to send with the request
        :param Optional[Dict[str,str]] additional_headers: Any additional headers to add to the request
        :param Optional[Any] json_data: The JSON data to send with the request
        :param bool stream: Set to True to stream the response back

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
            request_url, auth=self.credentials, headers=headers, json=json_data, stream=stream
        )

    @retry(
        retry=retry_if_exception(_is_connection_failure),
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
    def patch(
        self,
        request_url: str,
        *,
        operations: Optional[List[PatchOperation]] = None,
        json_data: Optional[Any] = None,
        additional_headers: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Issue a PATCH request with the correct credentials and headers.

        Note: If `json_data` and `operations` are not None, the latter will take
        precedence.

        :param str request_url: The URL to issue the request to
        :param Optional[Dict[str,str]] additional_headers: Any additional headers to add to the request
        :param Optional[Any] json_data: The JSON data to send with the request
        :param Optional[List[PatchOperation]] operations: The patch operations to send with the request

        :returns: The raw response object from the API
        """

        if operations is not None:
            json_data = [operation.serialize() for operation in operations]
            if additional_headers is None:
                additional_headers = {}
            if "Content-Type" not in additional_headers:
                additional_headers["Content-Type"] = "application/json-patch+json"

        headers = self.construct_headers(additional_headers=additional_headers)
        return self._session.patch(
            request_url, auth=self.credentials, headers=headers, json=json_data
        )

    @retry(
        retry=retry_if_exception(_is_connection_failure),
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
    def put(
        self,
        request_url: str,
        json_data: Optional[Any] = None,
        *,
        additional_headers: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Issue a PUT request with the correct credentials and headers.

        :param str request_url: The URL to issue the request to
        :param Optional[Dict[str,str]] additional_headers: Any additional headers to add to the request
        :param Optional[Dict[str,Any]] json_data: The JSON data to send with the request

        :returns: The raw response object from the API
        """
        headers = self.construct_headers(additional_headers=additional_headers)
        return self._session.put(
            request_url, auth=self.credentials, headers=headers, json=json_data
        )

    @retry(
        retry=retry_if_exception(_is_connection_failure),
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
    def delete(
        self, request_url: str, *, additional_headers: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Issue a DELETE request with the correct credentials and headers.

        :param str request_url: The URL to issue the request to
        :param Optional[Dict[str,str]] additional_headers: Any additional headers to add to the request

        :returns: The raw response object from the API
        """
        headers = self.construct_headers(additional_headers=additional_headers)
        return self._session.delete(request_url, auth=self.credentials, headers=headers)

    @retry(
        retry=retry_if_exception(_is_connection_failure),
        wait=wait_random_exponential(max=10),
        stop=stop_after_attempt(5),
    )
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
                f"ADO returned a non-200 status code, configuration={self}", response,
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

        for header_name, header_value in additional_headers.items():
            headers[header_name] = header_value

        return headers
