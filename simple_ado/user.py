#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO user API wrapper."""

import logging

from simple_ado.base_client import ADOBaseClient
from simple_ado.exceptions import ADOException
from simple_ado.http_client import ADOHTTPClient
from simple_ado.types import TeamFoundationId


class ADOUserClient(ADOBaseClient):
    """Wrapper class around the ADO user APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("user"))

    def get_team_foundation_id(self, identity: str) -> TeamFoundationId:
        """Fetch the unique Team Foundation GUID for a given identity.

        :param str identity: The identity to fetch for (should be email for users and display name for groups)

        :returns: The team foundation ID

        :raises ADOException: If we can't get the identity from the response
        """

        # TODO this should be in an identities space in the next major release

        request_url = self.http_client.graph_endpoint()
        request_url += f"/identities?searchFilter=General&filterValue={identity}"
        request_url += f"&queryMembership=None&api-version=6.0"

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        extracted = self.http_client.extract_value(response_data)

        if len(extracted) == 0:
            raise ADOException("Could not resolve identity: " + identity)

        if len(extracted) > 1:
            raise ADOException(f"Found multiple identities matching '{identity}'")

        return extracted[0]["id"]
