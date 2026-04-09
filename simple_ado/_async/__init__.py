#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO API wrapper (async)."""

import datetime
import logging
from typing import Any, AsyncIterator
import urllib.parse

from simple_ado._async import (
    audit,
    auth as auth_module,
    builds,
    endpoints,
    git,
    governance,
    graph,
    http_client,
    identities,
    pipelines,
    pools,
    pull_requests,
    security,
    user,
    wiki,
)
from simple_ado._async.auth.ado_auth import ADOAsyncAuth
from simple_ado._async.auth.ado_basic_auth import ADOAsyncBasicAuth
from simple_ado._async.auth.ado_token_auth import ADOAsyncTokenAuth
from simple_ado._async.auth.ado_azid_auth import ADOAsyncAzIDAuth
from simple_ado._async.audit import ADOAsyncAuditClient
from simple_ado._async.builds import ADOAsyncBuildClient
from simple_ado._async.endpoints import ADOAsyncEndpointsClient
from simple_ado.exceptions import ADOException, ADOHTTPException
from simple_ado._async.identities import ADOAsyncIdentitiesClient
from simple_ado._async.git import ADOAsyncGitClient
from simple_ado._async.graph import ADOAsyncGraphClient
from simple_ado._async.governance import ADOAsyncGovernanceClient
from simple_ado._async.http_client import ADOAsyncHTTPClient, ADOResponse
from simple_ado.models.pull_requests import ADOPullRequestTimeRangeType
from simple_ado._async.pipelines import ADOAsyncPipelineClient
from simple_ado._async.pools import ADOAsyncPoolsClient
from simple_ado._async.pull_requests import ADOAsyncPullRequestClient, ADOPullRequestStatus
from simple_ado._async.security import ADOAsyncSecurityClient
from simple_ado._async.user import ADOAsyncUserClient
from simple_ado._async.wiki import ADOAsyncWikiClient
from simple_ado._async.work_item import ADOAsyncWorkItem
from simple_ado._async.workitems import ADOAsyncWorkItemsClient

# Re-export submodules
from simple_ado import (
    ado_types,
    comments,
    exceptions,
    models,
)

# Re-export auth_module as auth to maintain public API
auth = auth_module

__all__ = [
    "ADOAsyncAuditClient",
    "ADOAsyncAuth",
    "ADOAsyncAzIDAuth",
    "ADOAsyncBasicAuth",
    "ADOAsyncBuildClient",
    "ADOAsyncEndpointsClient",
    "ADOException",
    "ADOAsyncGitClient",
    "ADOAsyncGovernanceClient",
    "ADOAsyncGraphClient",
    "ADOAsyncHTTPClient",
    "ADOHTTPException",
    "ADOAsyncIdentitiesClient",
    "ADOAsyncPipelineClient",
    "ADOAsyncPoolsClient",
    "ADOAsyncPullRequestClient",
    "ADOPullRequestStatus",
    "ADOPullRequestTimeRangeType",
    "ADOResponse",
    "ADOAsyncSecurityClient",
    "ADOAsyncTokenAuth",
    "ADOAsyncUserClient",
    "ADOAsyncWikiClient",
    "ADOAsyncWorkItem",
    "ADOAsyncWorkItemsClient",
    # Submodules
    "audit",
    "auth",
    "builds",
    "comments",
    "endpoints",
    "exceptions",
    "git",
    "governance",
    "graph",
    "http_client",
    "identities",
    "models",
    "pipelines",
    "pools",
    "pull_requests",
    "security",
    "ado_types",
    "user",
    "wiki",
]


class ADOAsyncClient:
    """Async wrapper class around the ADO API.

    :param tenant: The ADO tenant to connect to
    :param auth: The auth details to use for the API connection
    :param user_agent: The user agent to set
    :param extra_headers: Any extra headers which should be sent with the API requests
    :param log: The logger to use for logging (a new one will be used if one is not supplied)
    """

    # pylint: disable=too-many-instance-attributes

    log: logging.Logger

    http_client: ADOAsyncHTTPClient

    audit: ADOAsyncAuditClient
    builds: ADOAsyncBuildClient
    endpoints: ADOAsyncEndpointsClient
    git: ADOAsyncGitClient
    governance: ADOAsyncGovernanceClient
    graph: ADOAsyncGraphClient
    identities: ADOAsyncIdentitiesClient
    pipelines: ADOAsyncPipelineClient
    pools: ADOAsyncPoolsClient
    security: ADOAsyncSecurityClient
    user: ADOAsyncUserClient
    wiki: ADOAsyncWikiClient
    workitems: ADOAsyncWorkItemsClient

    def __init__(
        self,
        *,
        tenant: str,
        auth: ADOAsyncAuth,  # pylint: disable=redefined-outer-name
        user_agent: str | None = None,
        extra_headers: dict[str, str] | None = None,
        log: logging.Logger | None = None,
    ) -> None:
        """Construct a new client object."""

        if log is None:
            self.log = logging.getLogger("ado")
        else:
            self.log = log.getChild("ado")

        self.http_client = ADOAsyncHTTPClient(
            tenant=tenant,
            auth=auth,
            user_agent=user_agent if user_agent is not None else tenant,
            log=self.log,
            extra_headers=extra_headers,
        )

        self.audit = ADOAsyncAuditClient(self.http_client, self.log)
        self.builds = ADOAsyncBuildClient(self.http_client, self.log)
        self.endpoints = ADOAsyncEndpointsClient(self.http_client, self.log)
        self.identities = ADOAsyncIdentitiesClient(self.http_client, self.log)
        self.git = ADOAsyncGitClient(self.http_client, self.log)
        self.governance = ADOAsyncGovernanceClient(self.http_client, self.log)
        self.graph = ADOAsyncGraphClient(self.http_client, self.log)
        self.pipelines = ADOAsyncPipelineClient(self.http_client, self.log)
        self.pools = ADOAsyncPoolsClient(self.http_client, self.log)
        self.security = ADOAsyncSecurityClient(self.http_client, self.log)
        self.user = ADOAsyncUserClient(self.http_client, self.log)
        self.wiki = ADOAsyncWikiClient(self.http_client, self.log)
        self.workitems = ADOAsyncWorkItemsClient(self.http_client, self.log)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.http_client.close()

    async def __aenter__(self) -> "ADOAsyncClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def verify_access(self) -> bool:
        """Verify that we have access to ADO.

        :returns: True if we have access, False otherwise
        """

        request_url = (
            self.http_client.api_endpoint(is_default_collection=False) + "/projects?api-version=7.1"
        )

        try:
            response = await self.http_client.get(request_url)
            response_data = self.http_client.decode_response(response)
            self.http_client.extract_value(response_data)
        except ADOException:
            return False

        return True

    async def create_pull_request(
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
        request_url += "/pullRequests?api-version=7.1"

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

        response = await self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    def pull_request(
        self, pull_request_id: int, project_id: str, repository_id: str
    ) -> ADOAsyncPullRequestClient:
        """Get an ADOAsyncPullRequestClient for the PR identifier.

        :param pull_request_id: The ID of the pull request to create the client for
        :param project_id: The ID of the project the PR is in
        :param repository_id: The ID of repository the pull request is on

        :returns: A new ADOAsyncPullRequestClient for the pull request specified
        """
        return ADOAsyncPullRequestClient(
            self.http_client, self.log, pull_request_id, project_id, repository_id
        )

    # pylint: disable=too-many-locals,too-complex,too-many-branches
    async def list_all_pull_requests(
        self,
        *,
        project_id: str,
        top: int | None = None,
        creator_id: str | None = None,
        include_links: bool | None = None,
        max_time: datetime.datetime | None = None,
        min_time: datetime.datetime | None = None,
        query_time_range_type: ADOPullRequestTimeRangeType | None = None,
        repository_id: str | None = None,
        reviewer_id: str | None = None,
        branch_name: str | None = None,  # TODO: Rename to source_ref_name
        source_repo_id: str | None = None,
        pr_status: ADOPullRequestStatus | None = None,
        target_ref_name: str | None = None,
        title: str | None = None,
    ) -> AsyncIterator[Any]:
        """Get the pull requests matching the specified criteria from ADO.

        :param project_id: The ID of the project.
        :param top: The number of pull requests to retrieve per page.
        :param creator_id: If set, search for pull requests that were created by this identity (Team Foundation ID).
        :param include_links: Whether to include the _links field on the shallow references.
        :param max_time: If specified, filters pull requests that were created/closed before this date based on the
                         queryTimeRangeType specified.
        :param min_time: If specified, filters pull requests that were created/closed after this date based on the
                         queryTimeRangeType specified.
        :param query_time_range_type: The type of time range to use for min_time and max_time filtering. Defaults to
                                      Created if unset.
        :param repository_id: If set, search for pull requests whose target branch is in this repository.
        :param reviewer_id: If set, search for pull requests that have this identity as a reviewer (Team Foundation ID).
        :param branch_name: If set, search for pull requests from this source branch.
        :param source_repo_id: If set, search for pull requests whose source branch is in this repository.
        :param pr_status: If set, search for pull requests that are in this state. Defaults to Active if unset.
        :param target_ref_name: If set, search for pull requests into this target branch.
        :param title: If set, filters pull requests that contain the specified text in the title.

        :returns: An async iterator yielding pull request data dictionaries.
        """

        self.log.debug("Fetching PRs")

        offset = 0

        while True:
            request_url = (
                self.http_client.api_endpoint(project_id=project_id) + "/git/pullrequests?"
            )

            parameters: dict[str, Any] = {"$skip": offset, "api-version": "7.2-preview.2"}

            if top:
                parameters["$top"] = top

            if creator_id:
                parameters["searchCriteria.creatorId"] = creator_id

            if include_links is not None:
                parameters["searchCriteria.includeLinks"] = str(include_links).lower()

            if max_time:
                parameters["searchCriteria.maxTime"] = max_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            if min_time:
                parameters["searchCriteria.minTime"] = min_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            if query_time_range_type:
                parameters["searchCriteria.queryTimeRangeType"] = query_time_range_type.value

            if repository_id:
                parameters["searchCriteria.repositoryId"] = repository_id

            if reviewer_id:
                parameters["searchCriteria.reviewerId"] = reviewer_id

            if source_repo_id:
                parameters["searchCriteria.sourceRepositoryId"] = source_repo_id

            if pr_status:
                parameters["searchCriteria.status"] = pr_status.value

            if title:
                parameters["searchCriteria.title"] = title

            encoded_parameters = urllib.parse.urlencode(parameters)

            request_url += encoded_parameters

            # ADO doesn't like it if the `/` in branch references are encoded, so we just append them manually

            if branch_name is not None:
                request_url += (
                    f"&searchCriteria.sourceRefName={_canonicalize_branch_name(branch_name)}"
                )

            if target_ref_name is not None:
                request_url += (
                    f"&searchCriteria.targetRefName={_canonicalize_branch_name(target_ref_name)}"
                )

            response = await self.http_client.get(request_url)
            response_data = self.http_client.decode_response(response)

            extracted = self.http_client.extract_value(response_data)

            if len(extracted) == 0:
                break

            for item in extracted:
                yield item

            offset += len(extracted)

    # pylint: enable=too-many-locals,too-complex,too-many-branches

    async def custom_get(
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

        return await self.http_client.get(request_url)


def _canonicalize_branch_name(branch_name: str) -> str:
    """Cleanup the branch name before sending it via ADO request

    :param branch_name: The name of the branch to cleanup

    :returns: The cleaned up branch name to send via ADO request
    """
    if not branch_name.startswith("refs/heads/"):
        return "refs/heads/" + branch_name

    return branch_name
