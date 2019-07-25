#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO Git API wrapper."""

import enum
import logging
import os
from typing import Any, Dict, List, Optional
import urllib.parse

import requests

from simple_ado.base_client import ADOBaseClient
from simple_ado.context import ADOContext
from simple_ado.exceptions import ADOException, ADOHTTPException
from simple_ado.http_client import ADOHTTPClient, ADOResponse


class ADOGitStatusState(enum.Enum):
    """Possible values of git status states."""

    NOT_SET: str = "notSet"
    NOT_APPLICABLE: str = "notApplicable"
    PENDING: str = "pending"
    SUCCEEDED: str = "succeeded"
    FAILED: str = "failed"
    ERROR: str = "error"



class ADOReferenceUpdate:
    """Contains the relevant details about a reference update.

    :param name: The full name of the reference to update. e.g. refs/heads/my_branch
    :param old_object_id: The ID that the reference previously pointed to
    :param new_object_id: The ID that the reference should point to
    """

    name: str
    old_object_id: str
    new_object_id: str

    def __init__(self, name: str, old_object_id: Optional[str], new_object_id: Optional[str]) -> None:
        self.name = name

        if old_object_id:
            self.old_object_id = old_object_id
        else:
            self.old_object_id = "0000000000000000000000000000000000000000"

        if new_object_id:
            self.new_object_id = new_object_id
        else:
            self.new_object_id = "0000000000000000000000000000000000000000"

    def json_data(self) -> Dict[str, str]:
        """Return the JSON representation for sending to ADO.

        :returns: The JSON representation
        """

        return {
            "name": self.name,
            "oldObjectId": self.old_object_id,
            "newObjectId": self.new_object_id,
        }


class ADOGitClient(ADOBaseClient):
    """Wrapper class around the ADO Git APIs.

    :param context: The context information for the client
    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(
        self, context: ADOContext, http_client: ADOHTTPClient, log: logging.Logger
    ) -> None:
        super().__init__(context, http_client, log.getChild("git"))

    def all_repositories(self) -> ADOResponse:
        """Get a list of repositories in the project.

        :returns: The ADO response with the data in it
        """
        self.log.debug("Getting repositories")
        request_url = f"{self._http_client.base_url()}/git/repositories/?api-version=1.0"
        response = self._http_client.get(request_url)
        response_data = self._http_client.decode_response(response)
        return self._http_client.extract_value(response_data)

    def get_status(self, sha: str) -> ADOResponse:
        """Set a status on a PR.

        :param str sha: The SHA of the commit to add the status to.

        :returns: The ADO response with the data in it

        :raises ADOException: If the SHA is not the full version
        """

        self.log.debug(f"Getting status for sha: {sha}")

        if len(sha) != 40:
            raise ADOException("The SHA for a commit must be the full 40 character version")

        request_url = f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}/commits/{sha}/"
        request_url += "statuses?api-version=2.1"

        response = self._http_client.get(request_url)
        response_data = self._http_client.decode_response(response)
        return self._http_client.extract_value(response_data)

    def set_status(
        self,
        sha: str,
        state: ADOGitStatusState,
        identifier: str,
        description: str,
        *,
        target_url: Optional[str] = None,
    ) -> ADOResponse:
        """Set a status on a PR.

        :param str sha: The SHA of the commit to add the status to.
        :param ADOGitStatusState state: The state to set the status to.
        :param str identifier: A unique identifier for the status (so it can be changed later)
        :param str description: The text to show in the status
        :param target_url: An optional URL to set which is opened when the description is clicked.
        :type target_url: str or None

        :returns: The ADO response with the data in it

        :raises ADOException: If the SHA is not the full version, or the state is set to NOT_SET
        """

        self.log.debug(f"Setting status ({state}) on sha ({sha}): {identifier} -> {description}")

        if len(sha) != 40:
            raise ADOException("The SHA for a commit must be the full 40 character version")

        if state == ADOGitStatusState.NOT_SET:
            raise ADOException("The NOT_SET state cannot be used for statuses on commits")

        request_url = f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}/commits/{sha}/"
        request_url += "statuses?api-version=2.1"

        body = {
            "state": state.value,
            "description": description,
            "context": {"name": self._context.status_context, "genre": identifier},
        }

        if target_url is not None:
            body["targetUrl"] = target_url

        response = self._http_client.post(request_url, json_data=body)
        return self._http_client.decode_response(response)

    def diff_between_commits(self, base_commit: str, target_commit: str) -> ADOResponse:
        """Get the diff between two commits.

        :param base_commit: The full hash of the base commit to perform the diff against.
        :param target_commit: The full hash of the commit to perform the diff of.
        :type base_commit: str
        :type target_commit: str

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Fetching commit diff: {base_commit}..{target_commit}")

        request_url = f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}/diffs/commits?"
        request_url += f"api-version=1.0"
        request_url += f"&baseVersionType=commit"
        request_url += f"&baseVersion={base_commit}"
        request_url += f"&targetVersionType=commit"
        request_url += f"&targetVersion={target_commit}"

        response = self._http_client.get(request_url)
        return self._http_client.decode_response(response)

    def download_zip(self, branch: str, output_path: str) -> None:
        """Download the zip of the branch specified.

        :param str branch: The name of the branch to download.
        :param str output_path: The path to write the output to.

        :raises ADOException: If the output path already exists
        :raises ADOHTTPException: If we fail to fetch the zip for any reason
        """

        self.log.debug(f"Downloading branch: {branch}")
        request_url = (
            f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}/Items?"
        )

        parameters = {
            "path": "/",
            "versionDescriptor[versionOptions]": "0",
            "versionDescriptor[versionType]": "0",
            "versionDescriptor[version]": branch,
            "resolveLfs": "true",
            "$format": "zip",
            "api-version": "5.0-preview.1",
        }

        request_url += urllib.parse.urlencode(parameters)

        if os.path.exists(output_path):
            raise ADOException("The output path already exists")

        with requests.get(
            request_url,
            auth=self._http_client.credentials,
            headers=self._http_client.construct_headers(),
            stream=True,
        ) as response:

            chunk_size = 1024 * 16

            if response.status_code < 200 or response.status_code >= 300:
                raise ADOHTTPException("Failed to fetch zip", response)

            with open(output_path, "wb") as output_file:

                content_length_string = response.headers.get("content-length", "0")

                total_size = int(content_length_string)
                total_downloaded = 0

                for data in response.iter_content(chunk_size=chunk_size):
                    total_downloaded += len(data)
                    output_file.write(data)

                    if total_size != 0:
                        progress = int((total_downloaded * 100.0) / total_size)
                        self.log.info(f"Download progress: {progress}%")

    def get_refs(
            self,
            *,
            filter_startswith: Optional[str] = None,
            filter_contains: Optional[str] = None,
            include_links: Optional[bool] = None,
            include_statuses: Optional[bool] = None,
            include_my_branches: Optional[bool] = None,
            latest_statuses_only: Optional[bool] = None,
            peel_tags: Optional[bool] = None,
            top: Optional[int] = None,
            continuation_token: Optional[str] = None,
    ) -> ADOResponse:
        """Set a status on a PR.

        All non-specified options use the ADO default.

        :param Optional[str] filter_startswith: A filter to apply to the refs
                                                (starts with)
        :param Optional[str] filter_contains: A filter to apply to the refs
                                              (contains)
        :param Optional[bool] include_links: Specifies if referenceLinks should
                                             be included in the result
        :param Optional[bool] include_statuses: Includes up to the first 1000
                                                commit statuses for each ref
        :param Optional[bool] include_my_branches: Includes only branches that
                                                   the user owns, the branches
                                                   the user favorites, and the
                                                   default branch. Cannot be
                                                   combined with the filter
                                                   parameter.
        :param Optional[bool] latest_statuses_only: True to include only the tip
                                                    commit status for each ref.
                                                    This requires
                                                    `include_statuses` to be set
                                                    to `True`.
        :param Optional[bool] peel_tags: Annotated tags will populate the
                                         `PeeledObjectId` property.
        :param Optional[int] top: Maximum number of refs to return. It cannot be
                                  bigger than 1000. If it is not provided, but
                                  `continuation_token` is, top will default to
                                  100.
        :param Optional[str] continuation_token: The continuation token used for
                                                 pagination

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting refs")

        request_url = f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}/refs?"

        parameters: Dict[str, Any] = {}

        if filter_startswith:
            parameters["filter"] = filter_startswith

        if filter_contains:
            parameters["filterContains"] = filter_contains

        if include_links:
            parameters["includeLinks"] = "true" if include_links else "false"

        if include_statuses:
            parameters["includeStatuses"] = "true" if include_statuses else "false"

        if include_my_branches:
            parameters["includeMyBranches"] = "true" if include_my_branches else "false"

        if latest_statuses_only:
            parameters["latestStatusesOnly"] = "true" if latest_statuses_only else "false"

        if peel_tags:
            parameters["peelTags"] = "true" if peel_tags else "false"

        if top:
            parameters["$top"] = top

        if continuation_token:
            parameters["continuationToken"] = continuation_token

        request_url += urllib.parse.urlencode(parameters)

        if len(parameters) > 0:
            request_url += "&"

        request_url += "api-version=5.0"

        response = self._http_client.get(request_url)
        response_data = self._http_client.decode_response(response)
        return self._http_client.extract_value(response_data)

    def get_commit(
            self,
            commit_id: str,
            *,
            change_count: Optional[int] = None,
    ) -> ADOResponse:
        """Set a status on a PR.

        All non-specified options use the ADO default.

        :param str commit_id: The id of the commit
        :param Optional[int] change_count: The number of changes to include in
                                           the result

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting commit: {commit_id}")

        request_url = f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}"
        request_url += f"/commits/{commit_id}?api-version=5.0"

        if change_count:
            request_url += f"&changeCount={change_count}"

        response = self._http_client.get(request_url)
        return self._http_client.decode_response(response)

    def update_refs(self, updates: List[ADOReferenceUpdate]) -> ADOResponse:
        """Update a list of references.

        :param updates: The list of updates to make

        :returns: The ADO response with the data in it
        """

        self.log.debug("Updating references")

        request_url = f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}"
        request_url += "/refs?api-version=5.0"

        data = [update.json_data() for update in updates]

        response = self._http_client.post(request_url, json_data=data)
        response_data = self._http_client.decode_response(response)
        return self._http_client.extract_value(response_data)

    def delete_branch(self, branch_name: str, object_id: str) -> ADOResponse:
        """Delete a branch

        :param branch_name: The full name of the branch. e.g. refs/heads/my_branch
        :param object_id: The ID of the object the branch currently points to

        :returns: The ADO response
        """
        return self.update_refs([ADOReferenceUpdate(branch_name, object_id, None)])
