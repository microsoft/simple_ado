#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO Git API wrapper."""

import enum
import logging
import os
from typing import Any, Callable
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

    def __init__(self, name: str, old_object_id: str | None, new_object_id: str | None) -> None:
        self.name = name

        if old_object_id:
            self.old_object_id = old_object_id
        else:
            self.old_object_id = "0000000000000000000000000000000000000000"

        if new_object_id:
            self.new_object_id = new_object_id
        else:
            self.new_object_id = "0000000000000000000000000000000000000000"

    def json_data(self) -> dict[str, str]:
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

        :param project_id: The ID of the project

        :returns: The ADO response with the data in it
        """
        self.log.debug("Getting repositories")
        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/?api-version=1.0"
        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_repository(self, *, project_id: str, repository_id: str) -> ADOResponse:
        """Get a repository from the project.

        :param project_id: The ID of the project
        :param repository_id: The ID of the repository

        :returns: The ADO response with the data in it
        """
        self.log.debug(f"Getting repository {repository_id}")
        request_url = (
            f"{self.http_client.api_endpoint(project_id=project_id)}/git/"
            + f"repositories/{repository_id}?api-version=6.0"
        )
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def get_status(self, *, sha: str, project_id: str, repository_id: str) -> ADOResponse:
        """Set a status on a PR.

        :param sha: The SHA of the commit to add the status to.
        :param project_id: The ID of the project
        :param repository_id: The ID for the repository

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
        target_url: str | None = None,
    ) -> ADOResponse:
        """Set a status on a PR.

        :param sha: The SHA of the commit to add the status to.
        :param state: The state to set the status to.
        :param identifier: A unique identifier for the status (so it can be changed later)
        :param description: The text to show in the status
        :param project_id: The ID of the project
        :param repository_id: The ID for the repository
        :param context: The context to use for build status notifications
        :param target_url: An optional URL to set which is opened when the description is clicked.

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
        self,
        *,
        base_commit: str,
        target_commit: str,
        project_id: str,
        repository_id: str,
    ) -> ADOResponse:
        """Get the diff between two commits.

        :param base_commit: The full hash of the base commit to perform the diff against.
        :param target_commit: The full hash of the commit to perform the diff of.
        :param project_id: The ID of the project
        :param repository_id: The ID for the repository

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
        self,
        *,
        branch: str,
        path: str = "/",
        output_path: str,
        project_id: str,
        repository_id: str,
        callback: Callable[[int, int], None] | None = None,
    ) -> None:
        """Download the zip of the branch specified.

        :param branch: The name of the branch to download.
        :param path: The path in the repository to download.
        :param output_path: The path to write the output to.
        :param project_id: The ID of the project
        :param repository_id: The ID for the repository
        :param callback: The callback for download progress updates. First
                         parameter is bytes downloaded, second is total bytes.
                         The latter will be 0 if the content length is unknown.

        :raises ADOException: If the output path already exists
        :raises ADOHTTPException: If we fail to fetch the zip for any reason
        """

        self.log.debug(f"Downloading branch: {branch}")
        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/{repository_id}/Items?"

        parameters = {
            "path": path,
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
            download_from_response_stream(
                response=response,
                output_path=output_path,
                log=self.log,
                callback=callback,
            )

    # pylint: disable=too-many-locals
    def get_refs(
        self,
        *,
        project_id: str,
        repository_id: str,
        filter_startswith: str | None = None,
        filter_contains: str | None = None,
        include_links: bool | None = None,
        include_statuses: bool | None = None,
        include_my_branches: bool | None = None,
        latest_statuses_only: bool | None = None,
        peel_tags: bool | None = None,
        top: int | None = None,
        continuation_token: str | None = None,
    ) -> ADOResponse:
        """Set a status on a PR.

        All non-specified options use the ADO default.

        :param project_id: The ID of the project
        :param repository_id: The ID for the repository
        :param filter_startswith: A filter to apply to the refs
                                                (starts with)
        :param filter_contains: A filter to apply to the refs
                                              (contains)
        :param include_links: Specifies if referenceLinks should
                                             be included in the result
        :param include_statuses: Includes up to the first 1000
                                                commit statuses for each ref
        :param include_my_branches: Includes only branches that
                                                   the user owns, the branches
                                                   the user favorites, and the
                                                   default branch. Cannot be
                                                   combined with the filter
                                                   parameter.
        :param latest_statuses_only: True to include only the tip
                                                    commit status for each ref.
                                                    This requires
                                                    `include_statuses` to be set
                                                    to `True`.
        :param peel_tags: Annotated tags will populate the
                                         `PeeledObjectId` property.
        :param top: Maximum number of refs to return. It cannot be
                                  bigger than 1000. If it is not provided, but
                                  `continuation_token` is, top will default to
                                  100.
        :param continuation_token: The continuation token used for
                                                 pagination

        :returns: The ADO response with the data in it
        """

        # pylint: disable=too-complex

        self.log.debug("Getting refs")

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/{repository_id}/refs?"

        parameters: dict[str, Any] = {}

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

    def get_stats_for_branch(
        self, *, project_id: str, repository_id: str, branch_name: str
    ) -> ADOResponse:
        """Get the stats for a branch.

        :param project_id: The ID of the project
        :param repository_id: The ID for the repository
        :param branch_name: The name of the branch to get the stats for

        :returns: The ADO response with the data in it
        """

        self.log.debug("Getting stats")

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/{repository_id}"
        request_url += f"/stats/branches?name={branch_name}&api-version=6.0"

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def get_commit(
        self,
        *,
        commit_id: str,
        project_id: str,
        repository_id: str,
        change_count: int | None = None,
    ) -> ADOResponse:
        """Set a status on a PR.

        All non-specified options use the ADO default.

        :param commit_id: The id of the commit
        :param project_id: The ID of the project
        :param repository_id: The ID for the repository
        :param change_count: The number of changes to include in
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
        self,
        *,
        updates: list[ADOReferenceUpdate],
        project_id: str,
        repository_id: str,
    ) -> ADOResponse:
        """Update a list of references.

        :param updates: The list of updates to make
        :param project_id: The ID of the project
        :param repository_id: The ID for the repository

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
        :param project_id: The ID of the project
        :param repository_id: The ID for the repository

        :returns: The ADO response
        """
        return self.update_refs(
            updates=[ADOReferenceUpdate(branch_name, object_id, None)],
            project_id=project_id,
            repository_id=repository_id,
        )

    class VersionControlRecursionType(enum.Enum):
        """Specifies the level of recursion to use when getting an item."""

        FULL = "full"
        NONE = "none"
        ONE_LEVEL = "oneLevel"
        ONE_LEVEL_PLUS_NESTED_EMPTY_FOLDERS = "oneLevelPlusNestedEmptyFolders"

    class GitVersionOptions(enum.Enum):
        """Version options."""

        FIRST_PARENT = "firstParent"
        NONE = "none"
        PREVIOUS_CHANGE = "previousChange"

    class GitVersionType(enum.Enum):
        """Version type. Determines how the ID of an item is interpreted."""

        BRANCH = "branch"
        COMMIT = "commit"
        TAG = "tag"

    # pylint: disable=too-many-locals
    def get_item(
        self,
        *,
        project_id: str,
        repository_id: str,
        path: str | None = None,
        scope_path: str | None = None,
        recursion_level: VersionControlRecursionType | None = None,
        include_content_metadata: bool | None = None,
        latest_processed_changes: bool | None = None,
        version_options: GitVersionOptions | None = None,
        version: str | None = None,
        version_type: GitVersionType | None = None,
        include_content: bool | None = None,
        resolve_lfs: bool | None = None,
    ) -> ADOResponse:
        """Get a git item.

        All non-specified options use the ADO default.

        :param project_id: The ID of the project
        :param repository_id: The ID for the repository
        :param path: The item path. Either this or scope_path must be set.
        :param scope_path: The path scope. Either this or path must be set.
        :param recursion_level: The recursion level
        :param include_content_metadata: Set to include content metadata
        :param latest_processed_changes: Set to include the latest changes
        :param version_options: Specify additional modifiers to version
        :param version: Version string identifier (name of tag/branch, SHA1 of commit)
        :param version_type: Version type (branch, tag or commit).
        :param include_content: Set to true to include item content when requesting JSON
        :param resolve_lfs: Set to true to resolve LFS pointer files to resolve actual content

        :returns: The ADO response with the data in it
        """

        self.log.debug("Getting item")

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/{repository_id}/items?"

        parameters: dict[str, Any] = {"api-version": "5.1", "$format": "json"}

        if not scope_path and not path:
            raise ADOException("Either path or scope_path must be set")

        if scope_path and path:
            raise ADOException("Either path or scope_path must be set, not both")

        if path is not None:
            parameters["path"] = path

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

    # pylint: disable=too-many-locals,line-too-long,too-complex,too-many-branches
    def get_commits(
        self,
        *,
        project_id: str,
        repository_id: str,
        skip: int | None = None,
        top: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        from_commit_id: str | None = None,
        to_commit_id: str | None = None,
        author: str | None = None,
        user: str | None = None,
        exclude_deletes: bool | None = None,
        inlcude_links: bool | None = None,
        include_push_data: bool | None = None,
        include_user_image_url: bool | None = None,
        include_work_items: bool | None = None,
        item_path: str | None = None,
        item_version: str | None = None,
        item_version_options: GitVersionOptions | None = None,
        item_version_type: GitVersionType | None = None,
    ) -> ADOResponse:
        """Retrieve git commits for a project

        All non-specified options use the ADO default.

        :param project_id: The ID of the project
        :param repository_id: The ID for the repository
        :param skip: Number of entries to skip
        :param top: Maximum number of entries to retrieve
        :param from_date: If provided, only include history entries created after this date
        :param to_date: If provided, only include history entries created before this date
        :param from_commit_id: If provided, a lower bound for filtering commits alphabetically
        :param to_commit_id: If provided, an upper bound for filtering commits alphabetically
        :param author: Alias or display name of the author
        :param user: Alias or display name of the committer
        :param exclude_deletes: If itemPath is specified, determines whether to exclude delete entries of the specified path.
        :param inlcude_links: Whether to include the _links field on the shallow references
        :param include_push_data: Whether to include the push information
        :param include_user_image_url: Whether to include the image Url for committers and authors
        :param include_work_items: Whether to include linked work items
        :param item_path: Path of item to search under
        :param item_version: Version string identifier (name of tag/branch, SHA1 of commit)
        :param item_version_options: Version options - Specify additional modifiers to version (e.g Previous)
        :param item_version_type: Version type (branch, tag, or commit). Determines how Id is interpreted

        :returns: The ADO response with the data in it
        """
        self.log.debug("Getting commits")

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/git/repositories/{repository_id}/commits?"

        parameters: dict[str, Any] = {"api-version": "7.2-preview.2"}

        if skip is not None:
            parameters["$skip"] = skip

        if top is not None:
            parameters["$top"] = top

        if from_date is not None:
            parameters["fromDate"] = from_date

        if to_date is not None:
            parameters["toDate"] = to_date

        if from_commit_id is not None:
            parameters["fromCommitId"] = from_commit_id

        if to_commit_id is not None:
            parameters["toCommitId"] = to_commit_id

        if author is not None:
            parameters["author"] = author

        if user is not None:
            parameters["user"] = user

        if exclude_deletes is not None:
            parameters["excludeDeletes"] = exclude_deletes

        if inlcude_links is not None:
            parameters["includeLinks"] = inlcude_links

        if include_push_data is not None:
            parameters["includePushData"] = include_push_data

        if include_user_image_url is not None:
            parameters["includeUserImageUrl"] = include_user_image_url

        if include_work_items is not None:
            parameters["includeWorkItems"] = include_work_items

        if item_path is not None:
            parameters["itemPath"] = item_path

        if item_version is not None:
            parameters["itemVersion.version"] = item_version

        if item_version_options is not None:
            parameters["itemVersion.versionOptions"] = item_version_options.value

        if item_version_type is not None:
            parameters["itemVersion.versionType"] = item_version_type.value

        request_url += urllib.parse.urlencode(parameters)

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    # pylint: disable=too-many-locals,line-too-long,too-complex,too-many-branches

    class BlobFormat(enum.Enum):
        """The type of format to get a blob in."""

        JSON = "json"
        ZIP = "zip"
        TEXT = "text"
        OCTETSTREAM = "octetstream"

    def get_blob(
        self,
        *,
        blob_id: str,
        project_id: str,
        repository_id: str,
        blob_format: BlobFormat | None = None,
        download: bool | None = None,
        file_name: str | None = None,
        resolve_lfs: bool | None = None,
    ) -> Any:
        """Get a git item.

        All non-specified options use the ADO default.

        :param blob_id: The SHA1 of the blob
        :param project_id: The ID for the project
        :param repository_id: The ID for the repository
        :param blob_format: The format to get the blob in
        :param download: Set to True to download rather than get a response
        :param file_name: The file name to use for the download if download is set to True
        :param resolve_lfs: Set to true to resolve LFS pointer files to resolve actual content

        :returns: The data returned and the return type depends on what you set blob_format to
        """

        self.log.debug("Getting blob")

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, project_id=project_id
        )
        request_url += f"/git/repositories/{repository_id}/blobs/{blob_id}?"

        parameters: dict[str, Any] = {
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

        if blob_format == ADOGitClient.BlobFormat.TEXT:
            self.http_client.validate_response(response)
            return response.text

        if blob_format == ADOGitClient.BlobFormat.JSON:
            return self.http_client.decode_response(response)

        self.http_client.validate_response(response)
        return response.content

    def get_blobs(
        self,
        *,
        blob_ids: list[str],
        output_path: str,
        project_id: str,
        repository_id: str,
    ) -> ADOResponse:
        """Get a git item.

        All non-specified options use the ADO default.

        :param blob_ids: The SHA1s of the blobs
        :param output_path: The location to write out the zip to
        :param project_id: The ID for the project
        :param repository_id: The ID for the repository

        :raises FileExistsError: If the output path already exists
        """

        self.log.debug("Getting blobs")

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
