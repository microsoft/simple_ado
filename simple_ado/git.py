#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO Git API wrapper."""

import enum
import logging
import os
from typing import Optional
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
