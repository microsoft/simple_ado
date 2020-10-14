#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO build API wrapper."""

import json
import logging
from typing import Dict, Optional
import urllib.parse


from simple_ado.base_client import ADOBaseClient
from simple_ado.http_client import ADOHTTPClient, ADOResponse
from simple_ado.types import TeamFoundationId
from simple_ado.utilities import download_from_response_stream


class ADOBuildClient(ADOBaseClient):
    """Wrapper class around the ADO Build APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("build"))

    def queue_build(
        self,
        *,
        project_id: str,
        definition_id: int,
        source_branch: str,
        variables: Dict[str, str],
        requesting_identity: Optional[TeamFoundationId] = None,
    ) -> ADOResponse:
        """Queue a new build.

        :param str project_id: The ID of the project
        :param definition_id: The identity of the build definition to queue (can be a string)
        :param source_branch: The source branch for the build
        :param variables: A dictionary of variables to pass to the definition
        :param requesting_identity: The identity of the user who requested the build be queued

        :returns: The ADO response with the data in it
        """

        request_url = (
            f"{self.http_client.api_endpoint(project_id=project_id)}/build/builds?api-version=4.1"
        )
        variable_json = json.dumps(variables)

        self.log.debug(f"Queueing build ({definition_id}): {variable_json}")

        body = {
            "parameters": variable_json,
            "definition": {"id": definition_id},
            "sourceBranch": source_branch,
        }

        if requesting_identity:
            body["requestedFor"] = {"id": requesting_identity}

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    def build_info(self, *, project_id: str, build_id: int) -> ADOResponse:
        """Get the info for a build.

        :param str project_id: The ID of the project
        :param int build_id: The identifier of the build to get the info for

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/build/builds/{build_id}?api-version=4.1"
        )
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def get_artifact_info(
        self, *, project_id: str, build_id: int, artifact_name: str
    ) -> ADOResponse:
        """Fetch an artifacts details from a build.

        :param str project_id: The ID of the project
        :param build_id: The ID of the build
        :param artifact_name: The name of the artifact to fetch

        :returns: The ADO response with the data in it
        """

        parameters = {
            "artifactName": artifact_name,
            "api-version": "4.1",
        }

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/build/builds/{build_id}/artifacts?"
        request_url += urllib.parse.urlencode(parameters)

        self.log.debug(f"Fetching artifact {artifact_name} from build {build_id}...")

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def download_artifact(
        self, *, project_id: str, build_id: int, artifact_name: str, output_path: str
    ) -> None:
        """Download an artifact from a build.

        :param str project_id: The ID of the project
        :param build_id: The ID of the build
        :param artifact_name: The name of the artifact to fetch
        :param str output_path: The path to write the output to.
        """

        parameters = {
            "artifactName": artifact_name,
            "$format": "zip",
            "api-version": "4.1",
        }

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/build/builds/{build_id}/artifacts?"
        request_url += urllib.parse.urlencode(parameters)

        self.log.debug(f"Fetching artifact {artifact_name} from build {build_id}...")

        with self.http_client.get(request_url, stream=True) as response:
            download_from_response_stream(response=response, output_path=output_path, log=self.log)
