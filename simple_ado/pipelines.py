#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO pipeline API wrapper."""

import logging
from typing import Any, Iterator
import urllib.parse


from simple_ado.base_client import ADOBaseClient
from simple_ado.http_client import ADOHTTPClient, ADOResponse


class ADOPipelineClient(ADOBaseClient):
    """Wrapper class around the ADO Pipeline APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("pipeline"))

    def get_pipelines(
        self,
        *,
        top: int | None = None,
        order_by: str | None = None,
        project_id: str,
    ) -> Iterator[dict[str, Any]]:
        """Get all the pipelines in the project.

        Note: This hasn't been tested with continuation tokens.

        :param top: An optional integer to only get the top N pipelines
        :param order_by: A sort expression to use (defaults to "name asc")
        :param project_id: The ID of the project

        :returns: The pipelines in the project
        """

        parameters: dict[str, Any] = {"api-version": "7.1-preview.1"}

        if top:
            parameters["$top"] = top

        if order_by:
            parameters["orderBy"] = order_by

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/pipelines?"
        request_url += urllib.parse.urlencode(parameters)

        url = request_url

        while True:
            response = self.http_client.get(url)
            decoded = self.http_client.decode_response(response)
            yield from decoded["value"]

            if not decoded.get("hasMore"):
                return

            continuation_token = decoded["continuationToken"]
            url = request_url + f"&continuationToken={continuation_token}"

    def get_pipeline(
        self,
        *,
        project_id: str,
        pipeline_id: int,
        pipeline_version: int | None = None,
    ) -> ADOResponse:
        """Get the info for a pipeline.

        :param project_id: The ID of the project
        :param pipeline_id: The identifier of the pipeline to get the info for
        :param pipeline_version: The version of the pipeline to get the info for

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/pipelines/{pipeline_id}?api-version=7.1-preview.1"
        )

        if pipeline_version:
            request_url += f"pipelineVersion={pipeline_version}"

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def preview(
        self,
        *,
        project_id: str,
        pipeline_id: int,
        pipeline_version: int | None = None,
    ) -> str | None:
        """Queue a dry run of the pipeline to return the final yaml.

        :param project_id: The ID of the project
        :param pipeline_id: The identifier of the pipeline to get the info for
        :param pipeline_version: The version of the pipeline to get the info for

        :returns: The raw YAML generated after parsing the templates (None if it is not a YAML pipeline)
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/pipelines/{pipeline_id}/preview?api-version=7.1-preview.1"
        )

        if pipeline_version:
            request_url += f"pipelineVersion={pipeline_version}"

        body = {
            "previewRun": True,
        }

        response = self.http_client.post(request_url, json_data=body)
        data = self.http_client.decode_response(response)
        return data.get("finalYaml")

    def get_top_ten_thousand_runs(self, *, project_id: str, pipeline_id: int) -> ADOResponse:
        """Get the top 10,000 runs for a pipeline.

        :param project_id: The ID of the project
        :param pipeline_id: The identifier of the pipeline to get the runs for

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/pipelines/{pipeline_id}/runs?api-version=6.0-preview.1"
        )

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_run(self, *, project_id: str, pipeline_id: int, run_id: int) -> ADOResponse:
        """Get a pipeline run.

        :param project_id: The ID of the project
        :param pipeline_id: The identifier of the pipeline to get the run for
        :param run_id: The identifier of the run to get

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/pipelines/{pipeline_id}/runs/{run_id}?api-version=6.0-preview.1"
        )

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def run_pipeline(
        self,
        *,
        project_id: str,
        pipeline_id: int,
        pipeline_version: int | None = None,
        preview_run: bool = False,
        resources: dict[str, Any] | None = None,
        stages_to_skip: list[str] | None = None,
        template_parameters: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
    ) -> ADOResponse:
        """Run a pipeline.

        :param project_id: The ID of the project
        :param pipeline_id: The identifier of the pipeline to run
        :param pipeline_version: The version of the pipeline to run (leave unset to run latest)
        :param preview_run: If True, this will run a dry run of the pipeline to return the final yaml
        :param resources: The resources to use for the run. See https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/runs/run-pipeline?view=azure-devops-rest-6.1#runresourcesparameters
        :param stages_to_skip: A list of stages to skip if any
        :param template_parameters: The template parameters to use for the run. A map of keys to values.
        :param variables: The variables to use for the run. A map of strings to `Variable`. See: https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/runs/run-pipeline?view=azure-devops-rest-6.1#variable

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/pipelines/{pipeline_id}/runs?api-version=6.1-preview.1"
        )

        if pipeline_version:
            request_url += f"pipelineVersion={pipeline_version}"

        body = {"previewRun": preview_run}

        if resources:
            body["resources"] = resources

        if stages_to_skip:
            body["stagesToSkip"] = stages_to_skip

        if template_parameters:
            body["templateParameters"] = template_parameters

        if variables:
            body["variables"] = variables

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)
