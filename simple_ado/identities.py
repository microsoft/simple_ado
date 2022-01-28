#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO identities API wrapper."""

import logging
from typing import Any, cast, Dict, List

from simple_ado.base_client import ADOBaseClient
from simple_ado.exceptions import ADOException
from simple_ado.http_client import ADOHTTPClient
from simple_ado.types import TeamFoundationId


class ADOIdentitiesClient(ADOBaseClient):
    """Wrapper class around the ADO identities APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("user"))

    def search(self, identity: str) -> List[Dict[str, Any]]:
        """Fetch the unique Team Foundation GUID for a given identity.

        :param str identity: The identity to fetch for (should be email for users and display name for groups)

        :returns: The found identities

        :raises ADOException: If we can't get the identity from the response
        """

        request_url = self.http_client.graph_endpoint()
        request_url += f"/identities?searchFilter=General&filterValue={identity}"
        request_url += "&queryMembership=None&api-version=6.0"

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_team_foundation_id(self, identity: str) -> TeamFoundationId:
        """Fetch the unique Team Foundation GUID for a given identity.

        :param str identity: The identity to fetch for (should be email for users and display name for groups)

        :returns: The team foundation ID

        :raises ADOException: If we can't get the identity from the response
        """

        results = self.search(identity)

        if len(results) == 0:
            raise ADOException("Could not resolve identity: " + identity)

        if len(results) > 1:
            raise ADOException(f"Found multiple identities matching '{identity}'")

        result = results[0]

        return cast(TeamFoundationId, result["id"])
