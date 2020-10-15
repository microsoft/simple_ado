#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO Git API wrapper."""

import enum
import logging
import os
from typing import Any, Dict, List, Optional
import urllib.parse

from simple_ado.base_client import ADOBaseClient
from simple_ado.exceptions import ADOException
from simple_ado.http_client import ADOHTTPClient, ADOResponse
from simple_ado.utilities import download_from_response_stream


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

    def __init__(
        self, name: str, old_object_id: Optional[str], new_object_id: Optional[str]
    ) -> None:
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

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("git"))

    def all_repositories(self, project_id: str) -> ADOResponse:
        """Get a list of repositories in the project.

        :param str project_id: The ID of the project

        :returns: The ADO response with the data in it
        """
        self.log.debug("Getting repositories")
        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/?api-version=1.0"
        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_status(self, *, sha: str, project_id: str, repository_id: str) -> ADOResponse:
        """Set a status on a PR.

        :param str sha: The SHA of the commit to add the status to.
        :param str project_id: The ID of the project
        :param str repository_id: The ID for the repository

        :returns: The ADO response with the data in it

        :raises ADOException: If the SHA is not the full version
        """

        self.log.debug(f"Getting status for sha: {sha}")

        if len(sha) != 40:
            raise ADOException("The SHA for a commit must be the full 40 character version")

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/git/repositories/{repository_id}/commits/{sha}/statuses?api-version=2.1"
        )

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def set_status(
        self,
        *,
        sha: str,
        state: ADOGitStatusState,
        identifier: str,
        description: str,
        project_id: str,
        repository_id: str,
        context: str,
        target_url: Optional[str] = None,
    ) -> ADOResponse:
        """Set a status on a PR.

        :param str sha: The SHA of the commit to add the status to.
        :param ADOGitStatusState state: The state to set the status to.
        :param str identifier: A unique identifier for the status (so it can be changed later)
        :param str description: The text to show in the status
        :param str project_id: The ID of the project
        :param str repository_id: The ID for the repository
        :param str context: The context to use for build status notifications
        :param Optional[str] target_url: An optional URL to set which is opened when the description is clicked.

        :returns: The ADO response with the data in it

        :raises ADOException: If the SHA is not the full version, or the state is set to NOT_SET
        """

        self.log.debug(f"Setting status ({state}) on sha ({sha}): {identifier} -> {description}")

        if len(sha) != 40:
            raise ADOException("The SHA for a commit must be the full 40 character version")

        if state == ADOGitStatusState.NOT_SET:
            raise ADOException("The NOT_SET state cannot be used for statuses on commits")

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/git/repositories/{repository_id}/commits/{sha}/"
        )
        request_url += "statuses?api-version=2.1"

        body = {
            "state": state.value,
            "description": description,
            "context": {"name": context, "genre": identifier},
        }

        if target_url is not None:
            body["targetUrl"] = target_url

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    def diff_between_commits(
        self, *, base_commit: str, target_commit: str, project_id: str, repository_id: str,
    ) -> ADOResponse:
        """Get the diff between two commits.

        :param str base_commit: The full hash of the base commit to perform the diff against.
        :param str target_commit: The full hash of the commit to perform the diff of.
        :param str project_id: The ID of the project
        :param str repository_id: The ID for the repository

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Fetching commit diff: {base_commit}..{target_commit}")

        base_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/git/repositories/{repository_id}/diffs/commits?"
        )

        changes = []
        skip = 0

        while True:

            parameters = {
                "api-version": "5.1",
                "baseVersionType": "commit",
                "baseVersion": base_commit,
                "targetVersionType": "commit",
                "targetVersion": target_commit,
                "$skip": skip,
                "$top": 100,
            }

            request_url = base_url + urllib.parse.urlencode(parameters)

            response = self.http_client.get(request_url)
            data = self.http_client.decode_response(response)

            changes.extend(data["changes"])

            if data.get("allChangesIncluded", False):
                data["changes"] = changes
                return data

            skip += 100

    def download_zip(
        self, *, branch: str, output_path: str, project_id: str, repository_id: str,
    ) -> None:
        """Download the zip of the branch specified.

        :param str branch: The name of the branch to download.
        :param str output_path: The path to write the output to.
        :param str project_id: The ID of the project
        :param str repository_id: The ID for the repository

        :raises ADOException: If the output path already exists
        :raises ADOHTTPException: If we fail to fetch the zip for any reason
        """

        self.log.debug(f"Downloading branch: {branch}")
        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/{repository_id}/Items?"

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

        with self.http_client.get(request_url, stream=True) as response:
            download_from_response_stream(response=response, output_path=output_path, log=self.log)

    # pylint: disable=too-many-locals
    def get_refs(
        self,
        *,
        project_id: str,
        repository_id: str,
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

        :param str project_id: The ID of the project
        :param str repository_id: The ID for the repository
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

        # pylint: disable=too-complex

        self.log.debug(f"Getting refs")

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/{repository_id}/refs?"

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

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

        # pylint: enable=too-complex

    # pylint: enable=too-many-locals

    def get_commit(
        self,
        *,
        commit_id: str,
        project_id: str,
        repository_id: str,
        change_count: Optional[int] = None,
    ) -> ADOResponse:
        """Set a status on a PR.

        All non-specified options use the ADO default.

        :param str commit_id: The id of the commit
        :param str project_id: The ID of the project
        :param str repository_id: The ID for the repository
        :param Optional[int] change_count: The number of changes to include in
                                           the result

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting commit: {commit_id}")

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/{repository_id}"
        request_url += f"/commits/{commit_id}?api-version=5.0"

        if change_count:
            request_url += f"&changeCount={change_count}"

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def update_refs(
        self, *, updates: List[ADOReferenceUpdate], project_id: str, repository_id: str,
    ) -> ADOResponse:
        """Update a list of references.

        :param List[ADOReferenceUpdate] updates: The list of updates to make
        :param str project_id: The ID of the project
        :param str repository_id: The ID for the repository

        :returns: The ADO response with the data in it
        """

        self.log.debug("Updating references")

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/{repository_id}"
        request_url += "/refs?api-version=5.0"

        data = [update.json_data() for update in updates]

        response = self.http_client.post(request_url, json_data=data)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def delete_branch(
        self, branch_name: str, object_id: str, project_id: str, repository_id: str
    ) -> ADOResponse:
        """Delete a branch

        :param branch_name: The full name of the branch. e.g. refs/heads/my_branch
        :param object_id: The ID of the object the branch currently points to
        :param str project_id: The ID of the project
        :param str repository_id: The ID for the repository

        :returns: The ADO response
        """
        return self.update_refs(
            updates=[ADOReferenceUpdate(branch_name, object_id, None)],
            project_id=project_id,
            repository_id=repository_id,
        )

    class VersionControlRecursionType(enum.Enum):
        """Specifies the level of recursion to use when getting an item."""

        full = "full"
        none = "none"
        one_level = "oneLevel"
        one_level_plus_nested_empty_folders = "oneLevelPlusNestedEmptyFolders"

    class GitVersionOptions(enum.Enum):
        """Version options."""

        first_parent = "firstParent"
        none = "none"
        previous_change = "previousChange"

    class GitVersionType(enum.Enum):
        """Version type. Determines how the ID of an item is interpreted."""

        branch = "branch"
        commit = "commit"
        tag = "tag"

    # pylint: disable=too-many-locals
    def get_item(
        self,
        *,
        path: str,
        project_id: str,
        repository_id: str,
        scope_path: Optional[str] = None,
        recursion_level: Optional[VersionControlRecursionType] = None,
        include_content_metadata: Optional[bool] = None,
        latest_processed_changes: Optional[bool] = None,
        version_options: Optional[GitVersionOptions] = None,
        version: Optional[str] = None,
        version_type: Optional[GitVersionType] = None,
        include_content: Optional[bool] = None,
        resolve_lfs: Optional[bool] = None,
    ) -> ADOResponse:
        """Get a git item.

        All non-specified options use the ADO default.

        :param str path: The item path,
        :param str project_id: The ID of the project
        :param str repository_id: The ID for the repository
        :param Optional[str] scope_path: The path scope
        :param Optional[VersionControlRecursionType] recursion_level: The recursion level
        :param Optional[bool] include_content_metadata: Set to include content metadata
        :param Optional[bool] latest_processed_changes: Set to include the latest changes
        :param Optional[GitVersionOptions] version_options: Specify additional modifiers to version
        :param Optional[str] version: Version string identifier (name of tag/branch, SHA1 of commit)
        :param Optional[GitVersionType] version_type: Version type (branch, tag or commit).
        :param Optional[bool] include_content: Set to true to include item content when requesting JSON
        :param Optional[bool] resolve_lfs: Set to true to resolve LFS pointer files to resolve actual content

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting item")

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/{repository_id}/items?"

        parameters: Dict[str, Any] = {"path": path, "api-version": "5.1"}

        if scope_path is not None:
            parameters["scopePath"] = scope_path

        if recursion_level is not None:
            parameters["recursionLevel"] = recursion_level.value

        if include_content_metadata is not None:
            parameters["includeContentMetadata"] = "true" if include_content_metadata else "false"

        if latest_processed_changes is not None:
            parameters["latestProcessedChange"] = "true" if latest_processed_changes else "false"

        if version_options is not None:
            parameters["versionDescriptor.versionOptions"] = version_options.value

        if version is not None:
            parameters["versionDescriptor.version"] = version

        if version_type is not None:
            parameters["versionDescriptor.versionType"] = version_type.value

        if include_content is not None:
            parameters["includeContent"] = "true" if include_content else "false"

        if resolve_lfs is not None:
            parameters["resolveLfs"] = "true" if resolve_lfs else "false"

        request_url += urllib.parse.urlencode(parameters)

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    # pylint: enable=too-many-locals

    class BlobFormat(enum.Enum):
        """The type of format to get a blob in."""

        json = "json"
        zip = "zip"
        text = "text"
        octetstream = "octetstream"

    def get_blob(
        self,
        *,
        blob_id: str,
        project_id: str,
        repository_id: str,
        blob_format: Optional[BlobFormat] = None,
        download: Optional[bool] = None,
        file_name: Optional[str] = None,
        resolve_lfs: Optional[bool] = None,
    ) -> ADOResponse:
        """Get a git item.

        All non-specified options use the ADO default.

        :param str blob_id: The SHA1 of the blob
        :param str project_id: The ID for the project
        :param str repository_id: The ID for the repository
        :param Optional[BlobFormat] blob_format: The format to get the blob in
        :param Optional[bool] download: Set to True to download rather than get a response
        :param Optional[str] file_name: The file name to use for the download if download is set to True
        :param Optional[bool] resolve_lfs: Set to true to resolve LFS pointer files to resolve actual content

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting blob")

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, project_id=project_id
        )
        request_url += f"/git/repositories/{repository_id}/blobs/{blob_id}?"

        parameters: Dict[str, Any] = {
            "api-version": "5.1",
        }

        if blob_format is not None:
            parameters["$format"] = blob_format.value

        if download is not None:
            parameters["download"] = "true" if download else "false"

        if file_name is not None:
            parameters["fileName"] = file_name

        if resolve_lfs is not None:
            parameters["resolveLfs"] = "true" if resolve_lfs else "false"

        request_url += urllib.parse.urlencode(parameters)

        response = self.http_client.get(request_url)

        if blob_format == ADOGitClient.BlobFormat.text:
            self.http_client.validate_response(response)
            return response.text

        return self.http_client.decode_response(response)

    def get_blobs(
        self, *, blob_ids: List[str], output_path: str, project_id: str, repository_id: str,
    ) -> ADOResponse:
        """Get a git item.

        All non-specified options use the ADO default.

        :param List[str] blob_ids: The SHA1s of the blobs
        :param str output_path: The location to write out the zip to
        :param str project_id: The ID for the project
        :param str repository_id: The ID for the repository

        :raises FileExistsError: If the output path already exists
        """

        self.log.debug(f"Getting blobs")

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, project_id=project_id
        )
        request_url += f"/git/repositories/{repository_id}/blobs?api-version=5.1"

        if os.path.exists(output_path):
            raise FileExistsError("The output path already exists")

        with self.http_client.post(
            request_url,
            additional_headers={"Accept": "application/zip"},
            stream=True,
            json_data=blob_ids,
        ) as response:
            download_from_response_stream(response=response, output_path=output_path, log=self.log)
