#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO build API wrapper."""

import json
import logging
from typing import Any, Dict, Iterator, List, Optional, Union
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

    def get_builds(
        self,
        *,
        project_id: str,
        definitions: Optional[List[int]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Get the info for a build.

        :param str project_id: The ID of the project
        :param int definitions: An optional list of build definition IDs to filter on

        :returns: The ADO response with the data in it
        """

        request_url = self.http_client.api_endpoint(project_id=project_id) + "/build/builds/?"

        parameters = {
            "api-version": "4.1",
        }

        if definitions:
            parameters["definitions"] = ",".join(map(str, definitions))

        request_url += urllib.parse.urlencode(parameters)

        url = request_url

        while True:
            response = self.http_client.get(url)
            decoded = self.http_client.decode_response(response)
            yield from decoded["value"]

            continuation_token = response.headers.get(
                "X-MS-ContinuationToken", response.headers.get("x-ms-continuationtoken")
            )

            if not continuation_token:
                break

            url = request_url + f"&continuationToken={continuation_token}"

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

    def get_leases(self, *, project_id: str, build_id: int) -> ADOResponse:
        """Get the retention leases for a build.

        :param str project_id: The ID of the project
        :param build_id: The ID of the build

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/build/builds/{build_id}/leases?api-version=7.1-preview.1"
        )

        self.log.debug(f"Fetching leases for build {build_id}...")

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def delete_leases(self, *, project_id: str, lease_ids: Union[int, List[int]]) -> None:
        """Delete leases.

        :param str project_id: The ID of the project
        :param lease_ids: The IDs of the leases to delete
        """

        if isinstance(lease_ids, int):
            all_ids = [lease_ids]
        else:
            all_ids = lease_ids

        ids = ",".join(map(str, all_ids))

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/build/retention/leases?api-version=7.1-preview.2&ids={ids}"
        )

        self.log.debug(f"Deleting leases '{ids}'...")

        response = self.http_client.delete(request_url)
        self.http_client.validate_response(response)

    def delete_definition(self, *, project_id: str, definition_id: int) -> None:
        """Delete a definition and all associated builds.

        :param project_id: The ID of the project
        :param definition_id: The identifier of the definition to delete
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/build/definitions/{definition_id}?api-version=7.1-preview.7"
        )

        response = self.http_client.delete(request_url)
        self.http_client.validate_response(response)
