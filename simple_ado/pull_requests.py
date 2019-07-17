#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO Pull Request API wrapper."""

import logging
from typing import Any, Dict, List, Optional

import requests

from simple_ado.base_client import ADOBaseClient
from simple_ado.comments import (
    ADOComment,
    ADOCommentLocation,
    ADOCommentProperty,
    ADOCommentStatus,
)
from simple_ado.context import ADOContext
from simple_ado.exceptions import ADOException
from simple_ado.git import ADOGitStatusState
from simple_ado.http_client import ADOHTTPClient, ADOResponse, ADOThread


class ADOPullRequestClient(ADOBaseClient):
    """Wrapper class around the ADO Pull Request APIs.

    :param context: The context information for the client
    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    :param pull_request_id: The ID of the pull request
    """

    pull_request_id: int

    def __init__(
        self,
        context: ADOContext,
        http_client: ADOHTTPClient,
        log: logging.Logger,
        pull_request_id: int,
    ) -> None:
        self.pull_request_id = pull_request_id
        super().__init__(context, http_client, log.getChild(f"pr.{pull_request_id}"))

    def details(self) -> ADOResponse:
        """Get the details for the PR from ADO.

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting PR: {self.pull_request_id}")
        request_url = f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}"
        request_url += f"/pullRequests/{self.pull_request_id}?api-version=3.0-preview"
        response = self._http_client.get(request_url)
        return self._http_client.decode_response(response)

    def workitems(self) -> ADOResponse:
        """Get the workitems associated with the PR from ADO.

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting workitems: {self.pull_request_id}")
        request_url = f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}"
        request_url += f"/pullRequests/{self.pull_request_id}/workitems?api-version=5.0"
        response = self._http_client.get(request_url)
        return self._http_client.decode_response(response)

    def get_threads(self, *, include_deleted: bool = False) -> List[ADOThread]:
        """Get the comments on the PR from ADO.

        :param bool include_deleted: Set to True if deleted threads should be included.

        :returns: A list of ADOThreads that were found
        """

        self.log.debug(f"Getting threads: {self.pull_request_id}")
        request_url = f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}"
        request_url += f"/pullRequests/{self.pull_request_id}/threads?api-version=3.0-preview"
        response = self._http_client.get(request_url)
        response_data = self._http_client.decode_response(response)
        comments: List[ADOThread] = self._http_client.extract_value(response_data)

        if include_deleted:
            return comments

        return [comment for comment in comments if comment["isDeleted"] is False]

    def create_comment_with_text(
        self,
        comment_text: str,
        *,
        comment_location: Optional[ADOCommentLocation] = None,
        status: Optional[ADOCommentStatus] = None,
    ) -> ADOResponse:
        """Create a thread using a single root comment.

        :param str comment_text: The text to set in the comment.
        :param Optional[ADOCommentLocation] comment_location: The location to place the comment.
        :param Optional[ADOCommentStatus] status: The status of the comment

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Creating comment: ({self.pull_request_id}) {comment_text}")
        comment = ADOComment(comment_text, comment_location)
        return self.create_comment(comment, status=status)

    def create_comment(
        self, comment: ADOComment, *, status: Optional[ADOCommentStatus] = None
    ) -> ADOResponse:
        """Create a thread using a single root comment.

        :param ADOComment comment: The comment to add.
        :param Optional[ADOCommentStatus] status: The status of the comment

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Creating comment: ({self.pull_request_id}) {comment}")
        return self.create_thread(
            [comment.generate_representation()], thread_location=comment.location, status=status
        )

    def create_thread(
        self,
        comments: List[Dict[str, Any]],
        *,
        thread_location: Optional[ADOCommentLocation] = None,
        status: Optional[ADOCommentStatus] = None,
        comment_identifier: str = "",
    ) -> ADOResponse:
        """Create a thread on a PR.

        :param List[Dict[str,Any]] comments: The comments to add to the thread.
        :param Optional[ADOCommentLocation] thread_location: The location the thread should be added
        :param Optional[ADOCommentStatus] status: The status of the comment
        :param Optional[ADOCommentStatus] comment_identifier: A unique identifier for the comment
                                                              that can be used for identification at
                                                              a later date

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Creating thread ({self.pull_request_id})")

        request_url = f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}"
        request_url += f"/pullRequests/{self.pull_request_id}/threads?api-version=3.0-preview"

        properties = {
            ADOCommentProperty.SUPPORTS_MARKDOWN: ADOCommentProperty.create_bool(True),
            ADOCommentProperty.COMMENT_IDENTIFIER: ADOCommentProperty.create_string(comment_identifier),
        }

        body = {
            "comments": comments,
            "properties": properties,
            "status": status.value if status is not None else ADOCommentStatus.ACTIVE.value,
        }

        if thread_location is not None:
            body["threadContext"] = thread_location.generate_representation()

        response = self._http_client.post(request_url, json_data=body)
        return self._http_client.decode_response(response)

    def delete_thread(self, thread: ADOThread) -> None:
        """Delete a comment thread from a pull request.

        :param thread: The thread to delete
        """

        thread_id = thread["id"]

        self.log.debug(f"Deleting thread: ({self.pull_request_id}) {thread_id}")

        for comment in thread["comments"]:
            comment_id = comment["id"]
            self.log.debug(f"Deleting comment: {comment_id}")
            request_url = (
                f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}"
            )
            request_url += f"/pullRequests/{self.pull_request_id}/threads/{thread_id}"
            request_url += f"/comments/{comment_id}?api-version=3.0-preview"
            requests.delete(
                request_url,
                auth=self._http_client.credentials,
                headers=self._http_client.construct_headers(),
            )

    def create_thread_list(self, threads: List[ADOComment]) -> None:
        """Create a list of threads

        :param List[ADOComment] threads: The threads to create

        :raises ADOException: If a thread is not an ADO comment
        """

        self.log.debug(f"Setting threads on PR: {self.pull_request_id}")

        # Check the type of the input
        for thread in threads:
            if not isinstance(thread, ADOComment):
                raise ADOException("Thread was not an ADOComment: " + str(thread))

        for thread in threads:
            self.log.debug("Adding thread")
            self.create_comment(thread)

    def set_status(
        self,
        state: ADOGitStatusState,
        identifier: str,
        description: str,
        *,
        iteration: Optional[int] = None,
        target_url: Optional[str] = None,
    ) -> ADOResponse:
        """Set a status on a PR.

        :param ADOGitStatusState state: The state to set the status to.
        :param str identifier: A unique identifier for the status (so it can be changed later)
        :param str description: The text to show in the status
        :param Optional[int] iteration: The iteration of the PR to set the status on
        :param Optional[str] target_url: An optional URL to set which is opened when the description is clicked.

        :returns: The ADO response with the data in it
        """

        self.log.debug(
            f"Setting PR status ({state}) on PR ({self.pull_request_id}): {identifier} -> {description}"
        )

        request_url = f"{self._http_client.base_url()}/git/repositories/{self._context.repository_id}"
        request_url += f"/pullRequests/{self.pull_request_id}/statuses?api-version=4.0-preview"

        body = {
            "state": state.value,
            "description": description,
            "context": {"name": self._context.status_context, "genre": identifier},
        }

        if iteration is not None:
            body["iterationId"] = iteration

        if target_url is not None:
            body["targetUrl"] = target_url

        response = self._http_client.post(request_url, json_data=body)
        return self._http_client.decode_response(response)

    def _thread_matches_identifier(self, thread: ADOThread, identifier: str) -> bool:
        """Check if the ADO thread matches the user and identifier

        :param thread: The thread to check
        :param identifier: The identifier to check against

        :returns: True if the thread matches, False otherwise

        :raises ADOException: If we couldn't find the author or the properties
        """

        try:
            # Deleted threads can stay around if they have other comments, so we
            # check if it was deleted before we check anything else.
            if thread["comments"][0]["isDeleted"]:
                return False
        except Exception:
            # If it's not there, it's not set
            pass

        try:
            # It wasn't one of the specified users comments
            if thread["comments"][0]["author"]["uniqueName"] != self._context.username:
                return False
        except:
            raise ADOException(
                "Could not find comments.0.author.uniqueName in thread: " + str(thread)
            )

        try:
            properties = thread["properties"]
        except:
            raise ADOException("Could not find properties in thread: " + str(thread))

        if properties is None:
            return False

        comment_identifier = properties.get(ADOCommentProperty.COMMENT_IDENTIFIER)

        if comment_identifier is None:
            return False

        value = comment_identifier.get("$value")

        if value == identifier:
            return True

        return False

    def threads_with_identifier(self, identifier: str) -> List[ADOThread]:
        """Get the threads on a PR which begin with the prefix specified.

        :param str identifier: The identifier to look for threads with

        :returns: The list of threads matching the identifier

        :raises ADOException: If the response is in an unexpected format
        """

        self.log.debug(
            f'Fetching threads with identifier "{identifier}" on PR {self.pull_request_id}'
        )

        matching_threads = []

        for thread in self.get_threads():
            self.log.debug("Handling thread...")

            if self._thread_matches_identifier(thread, identifier):
                matching_threads.append(thread)

        return matching_threads

    def delete_threads_with_identifier(self, identifier: str) -> None:
        """Delete the threads on a PR which begin with the prefix specified.

        :param str identifier: The identifier property value to look for threads matching
        """

        self.log.debug(
            f'Deleting threads with identifier "{identifier}" on PR {self.pull_request_id}'
        )

        for thread in self.threads_with_identifier(identifier):
            self.log.debug(f"Deleting thread: {thread}")
            self.delete_thread(thread)
