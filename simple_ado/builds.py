#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO build API wrapper."""

import enum
import json
import logging
from typing import Any, Iterator
import urllib.parse


from simple_ado.base_client import ADOBaseClient
from simple_ado.exceptions import ADOHTTPException
from simple_ado.http_client import ADOHTTPClient, ADOResponse
from simple_ado.types import TeamFoundationId
from simple_ado.utilities import download_from_response_stream


class BuildQueryOrder(enum.Enum):
    """The order for the build queries to be returned in."""

    FINISH_TIME_ASCENDING = "finishTimeAscending"
    FINISH_TIME_DESCENDING = "finishTimeDescending"
    QUEUE_TIME_ASCENDING = "queueTimeAscending"
    QUEUE_TIME_DESCENDING = "queueTimeDescending"
    START_TIME_ASCENDING = "startTimeAscending"
    START_TIME_DESCENDING = "startTimeDescending"


class StageUpdateType(enum.Enum):
    """The type of update to perform on a stage."""

    RETRY = "retry"
    CANCEL = "cancel"


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
        variables: dict[str, str],
        requesting_identity: TeamFoundationId | None = None,
    ) -> ADOResponse:
        """Queue a new build.

        :param project_id: The ID of the project
        :param definition_id: The identity of the build definition to queue (can be a string)
        :param source_branch: The source branch for the build
        :param variables: A dictionary of variables to pass to the definition
        :param requesting_identity: The identity of the user who requested the build be queued

        :returns: The ADO response with the data in it
        """

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/build/builds?api-version=4.1"
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

        :param project_id: The ID of the project
        :param build_id: The identifier of the build to get the info for

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
        definitions: list[int] | None = None,
        order: BuildQueryOrder | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Get the info for a build.

        :param project_id: The ID of the project
        :param definitions: An optional list of build definition IDs to filter on
        :param order: The order of the builds to return

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id) + "/build/builds/?"
        )

        parameters = {
            "api-version": "4.1",
        }

        if definitions:
            parameters["definitions"] = ",".join(map(str, definitions))

        if order:
            parameters["queryOrder"] = order.value

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

    def list_artifacts(self, *, project_id: str, build_id: int) -> ADOResponse:
        """List the artifacts for a build.

        :param project_id: The ID of the project
        :param build_id: The ID of the build
        :returns: The ADO response with the data in it
        """
        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/build/builds/{build_id}/artifacts?api-version=7.2-preview.5"
        )

        self.log.debug(f"Fetching artifacts for build {build_id}...")

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_artifact_info(
        self, *, project_id: str, build_id: int, artifact_name: str
    ) -> ADOResponse:
        """Fetch an artifacts details from a build.

        :param project_id: The ID of the project
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

        :param project_id: The ID of the project
        :param build_id: The ID of the build
        :param artifact_name: The name of the artifact to fetch
        :param output_path: The path to write the output to.
        """

        parameters = {
            "artifactName": artifact_name,
            "$format": "zip",
            "api-version": "4.1",
        }

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/build/builds/{build_id}/artifacts?"
        request_url += urllib.parse.urlencode(parameters)

        self.log.debug(f"Fetching artifact {artifact_name} from build {build_id}...")

        # This now redirects to a totally different domain. Since the domain is changing, requests will not keep the
        # authentication headers. We need to handle the redirect ourselves to avoid this.
        response = self.http_client.get(
            request_url, stream=True, allow_redirects=False, set_accept_json=False
        )

        try:

            while True:
                if not response.is_redirect:
                    break

                location = response.headers.get("location")

                if not location:
                    raise ADOHTTPException(
                        f"ADO returned a redirect status code without a location header, configuration={self}",
                        response,
                    )

                location_components = urllib.parse.urlsplit(location)

                if not location_components.hostname.endswith(".visualstudio.com"):
                    raise ADOHTTPException(
                        "ADO returned a redirect status code with a location header that is not on visualstudio.com, "
                        + f"configuration={self}",
                        response,
                    )

                response = self.http_client.get(
                    location, stream=True, allow_redirects=False, set_accept_json=False
                )

            download_from_response_stream(
                response=response, output_path=output_path, log=self.log
            )

        except Exception as ex:
            try:
                if response:
                    response.close()
            except Exception:
                pass
            finally:
                raise ex

    def get_file_manifest(
        self,
        *,
        project_id: str,
        build_id: int,
        artifact_name: str,
        artifact_id: str,
    ) -> None:
        """Download an artifact from a build.

        :param project_id: The ID of the project
        :param build_id: The ID of the build
        :param artifact_name: The name of the artifact to fetch
        :param artifact_id: The ID of the artifact to download (artifact.resource.data)
        """

        parameters = {
            "artifactName": artifact_name,
            "fileId": artifact_id,
            "fileName": "",
            "api-version": "7.2-preview.5",
        }

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/build/builds/{build_id}/artifacts?"
        request_url += urllib.parse.urlencode(parameters)

        self.log.debug(
            f"Fetching file manifest from artifact {artifact_name} from build {build_id}..."
        )

        response = self.http_client.get(request_url)

        return self.http_client.decode_response(response)

    def download_file(
        self,
        *,
        project_id: str,
        build_id: int,
        artifact_name: str,
        file_id: str,
        file_name: str,
        output_path: str,
    ) -> None:
        """Download an artifact from a build.

        :param project_id: The ID of the project
        :param build_id: The ID of the build
        :param artifact_name: The name of the artifact to fetch
        :param file_id: The ID of the file to download
        :param file_name: The name of the file to download
        :param output_path: The path to write the output to.
        """

        parameters = {
            "artifactName": artifact_name,
            "fileId": file_id,
            "fileName": file_name,
            "api-version": "7.2-preview.5",
        }

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/build/builds/{build_id}/artifacts?"
        request_url += urllib.parse.urlencode(parameters)

        self.log.debug(
            f"Fetching file {file_name} from artifact {artifact_name} from build {build_id}..."
        )

        response = self.http_client.get(request_url, stream=True)

        try:
            download_from_response_stream(
                response=response, output_path=output_path, log=self.log
            )
        except Exception as ex:
            try:
                if response:
                    response.close()
            except Exception:
                pass
            finally:
                raise ex

    def get_leases(self, *, project_id: str, build_id: int) -> ADOResponse:
        """Get the retention leases for a build.

        :param project_id: The ID of the project
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

    def delete_leases(self, *, project_id: str, lease_ids: int | list[int]) -> None:
        """Delete leases.

        :param project_id: The ID of the project
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

    def get_definitions(self, *, project_id: str) -> ADOResponse:
        """Get all definitions

        :param project_id: The ID of the project

        :returns: The project's definitions
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + "/build/definitions?api-version=6.0"
        )

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_definition(self, *, project_id: str, definition_id: int) -> ADOResponse:
        """Get all definitions

        :param project_id: The ID of the project
        :param definition_id: The identifier of the definition to get

        :returns: A definition
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/build/definitions/{definition_id}?api-version=6.0"
        )

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

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

    def patch_stage(
        self,
        *,
        project_id: str,
        build_id: int,
        stage_name: str,
        force_retry_all_jobs: bool,
        state: StageUpdateType,
    ) -> None:
        """Re-run the failed jobs on a build.

        :param project_id: The ID of the project
        :param build_id: The identifier of the build to re-run the jobs on
        :param stage_name: The name (identifier) of the stage to re-run.
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/build/builds/{build_id}/stages/{stage_name}?api-version=7.1"
        )

        body = {"forceRetryAllJobs": force_retry_all_jobs, "state": state.value}

        response = self.http_client.patch(request_url, json_data=body)
        self.http_client.validate_response(response)

    def rerun_failed_jobs(
        self, *, project_id: str, build_id: int, stage_name: str
    ) -> None:
        """Re-run the failed jobs on a build.

        :param project_id: The ID of the project
        :param build_id: The identifier of the build to re-run the jobs on
        :param stage_name: The name (identifier) of the stage to re-run.
        """

        self.patch_stage(
            project_id=project_id,
            build_id=build_id,
            stage_name=stage_name,
            force_retry_all_jobs=False,
            state=StageUpdateType.RETRY,
        )
