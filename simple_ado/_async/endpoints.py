#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO service endpoints API wrapper (async)."""

import logging
from typing import Any, AsyncIterator
import urllib.parse


from simple_ado._async.base_client import ADOAsyncBaseClient
from simple_ado._async.http_client import ADOAsyncHTTPClient, ADOResponse


class ADOAsyncEndpointsClient(ADOAsyncBaseClient):
    """Wrapper class around the ADO service endpoints APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOAsyncHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("endpoints"))

    async def get_endpoints(
        self, project_id: str, *, endpoint_type: str | None = None
    ) -> ADOResponse:
        """Gets the service endpoints.

        :param project_id: The identifier for the project
        :param endpoint_type: The type to filter down to.

        :returns: The ADO response with the data in it
        """
        request_url = (
            self.http_client.api_endpoint(project_id=project_id) + "/serviceendpoint/endpoints?"
        )

        parameters = {"api-version": "7.1"}

        if endpoint_type:
            parameters["type"] = endpoint_type

        request_url += urllib.parse.urlencode(parameters)

        response = await self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    async def get_usage_history(
        self, *, project_id: str, endpoint_id: str, top: int | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Gets the usage history for an endpoint.

        :param project_id: The identifier for the project
        :param endpoint_id: The endpoint to get the history for
        :param top: If set, get this number of results

        :returns: The ADO response with the data in it
        """
        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/serviceendpoint/{endpoint_id}/executionhistory?"
        )

        parameters: dict[str, Any] = {"api-version": "7.1"}

        if not top or top < 50:
            parameters["top"] = top
        else:
            parameters["top"] = 50

        request_url += urllib.parse.urlencode(parameters)

        url = request_url

        returned = 0

        while True:
            response = await self.http_client.get(url)
            decoded = self.http_client.decode_response(response)
            for use in decoded["value"]:
                yield use
                returned += 1

                if top and returned >= top:
                    return

            if "X-MS-ContinuationToken" not in response.headers:
                return

            continuation_token = response.headers["X-MS-ContinuationToken"]
            url = request_url + f"&continuationToken={continuation_token}"
