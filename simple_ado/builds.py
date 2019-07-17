#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO build API wrapper."""

import json
import logging
from typing import Dict, Optional


from simple_ado.base_client import ADOBaseClient
from simple_ado.context import ADOContext
from simple_ado.http_client import ADOHTTPClient, ADOResponse
from simple_ado.types import TeamFoundationId


class ADOBuildClient(ADOBaseClient):
    """Wrapper class around the ADO Build APIs.

    :param context: The context information for the client
    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(
        self, context: ADOContext, http_client: ADOHTTPClient, log: logging.Logger
    ) -> None:
        super().__init__(context, http_client, log.getChild("build"))

    def queue_build(
        self, definition_id: int, source_branch: str, variables: Dict[str, str], requesting_identity: Optional[TeamFoundationId]
    ) -> ADOResponse:
        """Queue a new build.

        :param definition_id: The identity of the build definition to queue (can be a string)
        :param source_branch: The source branch for the build
        :param variables: A dictionary of variables to pass to the definition
        :param requesting_identity: The identity of the user who requested the build be queued

        :returns: The ADO response with the data in it
        """

        request_url = f"{self._http_client.base_url()}/build/builds?api-version=4.1"
        variable_json = json.dumps(variables)

        self.log.debug(f"Queueing build ({definition_id}): {variable_json}")

        body = {
            "parameters": variable_json,
            "definition": {"id": definition_id},
            "sourceBranch": source_branch,
        }

        if requesting_identity:
            body["requestedFor"] = requesting_identity

        response = self._http_client.post(request_url, json_data=body)
        return self._http_client.decode_response(response)

    def build_info(self, build_id: int) -> ADOResponse:
        """Get the info for a build.

        :param int build_id: The identifier of the build to get the info for

        :returns: The ADO response with the data in it
        """

        request_url = f"{self._http_client.base_url()}/build/builds/{build_id}?api-version=4.1"
        response = self._http_client.get(request_url)
        return self._http_client.decode_response(response)
