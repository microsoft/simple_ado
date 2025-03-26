#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO API wrapper."""

import logging
from typing import Any, Iterator
import urllib.parse

import requests

from simple_ado.auth.ado_auth import ADOAuth
from simple_ado.auth.ado_basic_auth import ADOBasicAuth
from simple_ado.auth.ado_token_auth import ADOTokenAuth
from simple_ado.audit import ADOAuditClient
from simple_ado.builds import ADOBuildClient
from simple_ado.endpoints import ADOEndpointsClient
from simple_ado.exceptions import ADOException
from simple_ado.identities import ADOIdentitiesClient
from simple_ado.git import ADOGitClient
from simple_ado.graph import ADOGraphClient
from simple_ado.governance import ADOGovernanceClient
from simple_ado.http_client import ADOHTTPClient, ADOResponse
from simple_ado.pipelines import ADOPipelineClient
from simple_ado.pools import ADOPoolsClient
from simple_ado.pull_requests import ADOPullRequestClient, ADOPullRequestStatus
from simple_ado.security import ADOSecurityClient
from simple_ado.user import ADOUserClient
from simple_ado.wiki import ADOWikiClient
from simple_ado.workitems import ADOWorkItemsClient


class ADOClient:
    """Wrapper class around the ADO API.

    :param tenant: The ADO tenant to connect to
    :param auth: The auth details to use for the API connection
    :param user_agent: The user agent to set
    :param extra_headers: Any extra headers which should be sent with the API requests
    :param log: The logger to use for logging (a new one will be used if one is not supplied)
    """

    # pylint: disable=too-many-instance-attributes

    log: logging.Logger

    http_client: ADOHTTPClient

    audit: ADOAuditClient
    builds: ADOBuildClient
    endpoints: ADOEndpointsClient
    git: ADOGitClient
    governance: ADOGovernanceClient
    graph: ADOGraphClient
    identities: ADOIdentitiesClient
    pipelines: ADOPipelineClient
    pools: ADOPoolsClient
    security: ADOSecurityClient
    user: ADOUserClient
    wiki: ADOWikiClient
    workitems: ADOWorkItemsClient

    def __init__(
        self,
        *,
        tenant: str,
        auth: ADOAuth,
        user_agent: str | None = None,
        extra_headers: dict[str, str] | None = None,
        log: logging.Logger | None = None,
    ) -> None:
        """Construct a new client object."""

        if log is None:
            self.log = logging.getLogger("ado")
        else:
            self.log = log.getChild("ado")

        self.http_client = ADOHTTPClient(
            tenant=tenant,
            auth=auth,
            user_agent=user_agent if user_agent is not None else tenant,
            log=self.log,
            extra_headers=extra_headers,
        )

        self.audit = ADOAuditClient(self.http_client, self.log)
        self.builds = ADOBuildClient(self.http_client, self.log)
        self.endpoints = ADOEndpointsClient(self.http_client, self.log)
        self.identities = ADOIdentitiesClient(self.http_client, self.log)
        self.git = ADOGitClient(self.http_client, self.log)
        self.governance = ADOGovernanceClient(self.http_client, self.log)
        self.graph = ADOGraphClient(self.http_client, self.log)
        self.pipelines = ADOPipelineClient(self.http_client, self.log)
        self.pools = ADOPoolsClient(self.http_client, self.log)
        self.security = ADOSecurityClient(self.http_client, self.log)
        self.user = ADOUserClient(self.http_client, self.log)
        self.wiki = ADOWikiClient(self.http_client, self.log)
        self.workitems = ADOWorkItemsClient(self.http_client, self.log)

    def verify_access(self) -> bool:
        """Verify that we have access to ADO.

        :returns: True if we have access, False otherwise
        """

        request_url = (
            self.http_client.api_endpoint(is_default_collection=False) + "/projects?api-version=6.0"
        )

        try:
            response = self.http_client.get(request_url)
            response_data = self.http_client.decode_response(response)
            self.http_client.extract_value(response_data)
        except ADOException:
            return False

        return True

    def create_pull_request(
        self,
        *,
        source_branch: str,
        target_branch: str,
        project_id: str,
        repository_id: str,
        title: str | None = None,
        description: str | None = None,
        reviewer_ids: list[str] | None = None,
    ) -> ADOResponse:
        """Creates a pull request with the given information

        :param source_branch: The source branch of the pull request
        :param target_branch: The target branch of the pull request
        :param project_id: The ID of the project
        :param repository_id: The ID for the repository
        :param title: The title of the pull request
        :param description: The description of the pull request
        :param reviewer_ids: The reviewer IDs to be added to the pull request

        :returns: The ADO response with the data in it

        :raises ADOException: If we fail to create the pull request
        """
        self.log.debug("Creating pull request")

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/{repository_id}"
        request_url += "/pullRequests?api-version=5.1"

        body: dict[str, Any] = {
            "sourceRefName": _canonicalize_branch_name(source_branch),
            "targetRefName": _canonicalize_branch_name(target_branch),
        }

        if title is not None:
            body["title"] = title

        if description is not None:
            body["description"] = description

        if reviewer_ids is not None and len(reviewer_ids) > 0:
            body["reviewers"] = [{"id": reviewer_id} for reviewer_id in reviewer_ids]

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    def pull_request(
        self, pull_request_id: int, project_id: str, repository_id: str
    ) -> ADOPullRequestClient:
        """Get an ADOPullRequestClient for the PR identifier.

        :param pull_request_id: The ID of the pull request to create the client for
        :param project_id: The ID of the project the PR is in
        :param repository_id: The ID of repository the pull request is on

        :returns: A new ADOPullRequest client for the pull request specified
        """
        return ADOPullRequestClient(
            self.http_client, self.log, pull_request_id, project_id, repository_id
        )

    def list_all_pull_requests(
        self,
        *,
        branch_name: str | None = None,
        project_id: str,
        repository_id: str,
        top: int | None = None,
        pr_status: ADOPullRequestStatus | None = None,
    ) -> Iterator[Any]:
        """Get the pull requests for a branch from ADO.

        :param branch_name: The name of the branch to fetch the pull requests for.
        :param project_id: The ID of the project
        :param repository_id: The ID for the repository
        :param top: How many PRs to retrieve
        :param pr_status: Set to filter by only PRs with that status

        :returns: The ADO Response with the pull request data
        """

        self.log.debug("Fetching PRs")

        offset = 0

        while True:
            request_url = (
                self.http_client.api_endpoint(project_id=project_id)
                + f"/git/repositories/{repository_id}/pullRequests?"
            )

            parameters: dict[str, Any] = {"$skip": offset}

            if top:
                parameters["$top"] = top

            if pr_status:
                parameters["searchCriteria.status"] = pr_status.value

            encoded_parameters = urllib.parse.urlencode(parameters)

            request_url += encoded_parameters

            if branch_name is not None:
                request_url += (
                    f"&searchCriteria.sourceRefName={_canonicalize_branch_name(branch_name)}"
                )

            request_url += "&api-version=3.0-preview"

            response = self.http_client.get(request_url)
            response_data = self.http_client.decode_response(response)

            extracted = self.http_client.extract_value(response_data)

            if len(extracted) == 0:
                break

            yield from extracted

            offset += len(extracted)

    def custom_get(
        self,
        *,
        url_fragment: str,
        parameters: dict[str, Any],
        is_default_collection: bool = True,
        is_internal: bool = False,
        subdomain: str | None = None,
        project_id: str | None = None,
    ) -> ADOResponse:
        """Perform a custom GET REST request.

        We don't always expose everything that would be preferred to the end
        user, so to make it a little easier, we expose this method which lets
        the user perform an arbitrary GET request, but where we supply the base
        information.

        We only support GET requests as anything else is too complex to be
        exposed in a generic manner. For these cases, the requests should be
        built manually.

        :param url_fragment: The part of the URL that comes after `_apis/`
        :param parameters: The URL parameters to append
        :param is_default_collection: Whether this URL should start with the path "/DefaultCollection"
        :param is_internal: Whether this URL should use internal API endpoint "/_api"
        :param subdomain: A subdomain that should be used (if any)
        :param project_id: The project ID (if required)

        :returns: The raw response
        """

        encoded_parameters = urllib.parse.urlencode(parameters)
        request_url = self.http_client.api_endpoint(
            is_default_collection=is_default_collection,
            is_internal=is_internal,
            subdomain=subdomain,
            project_id=project_id,
        )
        request_url += f"/{url_fragment}?{encoded_parameters}"

        return self.http_client.get(request_url)


def _canonicalize_branch_name(branch_name: str) -> str:
    """Cleanup the branch name before sending it via ADO request

    :param branch_name: The name of the branch to cleanup

    :returns: The cleaned up branch name to send via ADO request
    """
    if not branch_name.startswith("refs/heads/"):
        return "refs/heads/" + branch_name

    return branch_name
