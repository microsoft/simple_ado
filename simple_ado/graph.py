# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO graph API wrapper."""

import logging
from typing import Any, List


from simple_ado.base_client import ADOBaseClient
from simple_ado.http_client import ADOHTTPClient, ADOResponse


class ADOGraphClient(ADOBaseClient):
    """Wrapper class around the ADO Graph APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("graph"))

    def list_groups(self) -> List[Any]:
        """Get the groups in the organization.

        :returns: The ADO response with the data in it
        """

        request_url = f"{self.http_client.graph_endpoint()}/graph/groups?api-version=5.1-preview.1"

        groups: List[Any] = []
        continuation_token = None

        while True:
            if continuation_token:
                url = request_url + f"&continuationToken={continuation_token}"
            else:
                url = request_url

            response = self.http_client.get(url)
            decoded = self.http_client.decode_response(response)
            groups += decoded["value"]

            if "X-MS-ContinuationToken" not in response.headers:
                break

            continuation_token = response.headers["X-MS-ContinuationToken"]

        return groups

    def get_group(self, descriptor: str) -> ADOResponse:
        """Get the group

        :param descriptor: The descriptor for the group

        :returns: The ADO response with the data in it
        """

        request_url = f"{self.http_client.graph_endpoint()}/graph/groups"
        request_url += f"/{descriptor}?api-version=5.1-preview.1"
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def get_user(self, descriptor: str) -> ADOResponse:
        """Get the user

        :param descriptor: The descriptor for the user

        :returns: The ADO response with the data in it
        """

        request_url = f"{self.http_client.graph_endpoint()}/graph/users"
        request_url += f"/{descriptor}?api-version=5.1-preview.1"
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)
