#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO Pull Request API wrapper."""

import enum
import logging
from typing import Any

import deserialize
import requests

from simple_ado.base_client import ADOBaseClient
from simple_ado.comments import (
    ADOComment,
    ADOCommentLocation,
    ADOCommentProperty,
    ADOCommentStatus,
)
from simple_ado.exceptions import ADOException
from simple_ado.git import ADOGitStatusState
from simple_ado.http_client import ADOHTTPClient, ADOResponse, ADOThread

from simple_ado.models import (
    PatchOperation,
    AddOperation,
    DeleteOperation,
    PropertyValue,
)


class ADOPullRequestStatus(enum.Enum):
    """Possible values of pull request states."""

    ABANDONED: str = "abandoned"
    ACTIVE: str = "active"
    ALL: str = "all"
    COMPLETED: str = "completed"
    NOT_SET: str = "notSet"


class ADOPullRequestClient(ADOBaseClient):
    """Wrapper class around the ADO Pull Request APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    :param pull_request_id: The ID of the pull request
    :param project_id: The ID of the project the PR is in
    :param repository_id: The ID of the repository the PR is for
    """

    pull_request_id: int
    project_id: str
    repository_id: str

    def __init__(
        self,
        http_client: ADOHTTPClient,
        log: logging.Logger,
        pull_request_id: int,
        project_id: str,
        repository_id: str,
    ) -> None:
        self.pull_request_id = pull_request_id
        self.repository_id = repository_id
        self.project_id = project_id
        super().__init__(http_client, log.getChild(f"pr.{pull_request_id}"))

    def details(self) -> ADOResponse:
        """Get the details for the PR from ADO.

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting PR: {self.pull_request_id}")
        request_url = (
            self.http_client.api_endpoint(project_id=self.project_id)
            + f"/git/repositories/{self.repository_id}"
            + f"/pullRequests/{self.pull_request_id}?api-version=3.0-preview"
        )
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def workitems(self) -> ADOResponse:
        """Get the workitems associated with the PR from ADO.

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting workitems: {self.pull_request_id}")
        request_url = (
            self.http_client.api_endpoint(project_id=self.project_id)
            + f"/git/repositories/{self.repository_id}"
            + f"/pullRequests/{self.pull_request_id}/workitems?api-version=5.0"
        )
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def iterations(self) -> ADOResponse:
        """Get the iterations of this PR.

        :returns: The ADO response with the iterations data in it
        """
        self.log.debug(f"Getting iterations: {self.pull_request_id}")
        request_url = (
            self.http_client.api_endpoint(project_id=self.project_id)
            + f"/git/repositories/{self.repository_id}"
            + f"/pullRequests/{self.pull_request_id}/iterations?api-version=6.0"
        )
        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_threads(self, *, include_deleted: bool = False) -> list[ADOThread]:
        """Get the comments on the PR from ADO.

        :param include_deleted: Set to True if deleted threads should be included.

        :returns: A list of ADOThreads that were found
        """

        self.log.debug(f"Getting threads: {self.pull_request_id}")
        request_url = (
            self.http_client.api_endpoint(project_id=self.project_id)
            + f"/git/repositories/{self.repository_id}"
            + f"/pullRequests/{self.pull_request_id}/threads?api-version=3.0-preview"
        )
        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        comments: list[ADOThread] = self.http_client.extract_value(response_data)

        if include_deleted:
            return comments

        return [comment for comment in comments if comment["isDeleted"] is False]

    def create_comment_with_text(
        self,
        comment_text: str,
        *,
        comment_location: ADOCommentLocation | None = None,
        status: ADOCommentStatus | None = None,
        comment_identifier: str | None = None,
    ) -> ADOResponse:
        """Create a thread using a single root comment.

        :param comment_text: The text to set in the comment.
        :param comment_location: The location to place the comment.
        :param status: The status of the comment
        :param comment_identifier: A unique identifier for the comment that can be used for identification
                                                 at a later date

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Creating comment: ({self.pull_request_id}) {comment_text}")
        comment = ADOComment(comment_text, comment_location)
        return self.create_comment(
            comment,
            status=status,
            comment_identifier=comment_identifier,
        )

    def create_comment(
        self,
        comment: ADOComment,
        *,
        status: ADOCommentStatus | None = None,
        comment_identifier: str | None = None,
    ) -> ADOResponse:
        """Create a thread using a single root comment.

        :param comment: The comment to add.
        :param status: The status of the comment
        :param comment_identifier: A unique identifier for the comment that can be used for identification
                                                 at a later date

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Creating comment: ({self.pull_request_id}) {comment}")
        return self.create_thread(
            comments=[comment.generate_representation()],
            thread_location=comment.location,
            status=status,
            comment_identifier=comment_identifier,
        )

    def create_thread(
        self,
        *,
        comments: list[dict[str, Any]],
        thread_location: ADOCommentLocation | None = None,
        status: ADOCommentStatus | None = None,
        comment_identifier: str | None = None,
    ) -> ADOResponse:
        """Create a thread on a PR.

        :param comments: The comments to add to the thread.
        :param thread_location: The location the thread should be added
        :param status: The status of the comment
        :param comment_identifier: A unique identifier for the comment that can be used for identification
                                                 at a later date

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Creating thread ({self.pull_request_id})")

        request_url = (
            self.http_client.api_endpoint(project_id=self.project_id)
            + f"/git/repositories/{self.repository_id}"
            + f"/pullRequests/{self.pull_request_id}/threads?api-version=3.0-preview"
        )

        properties = {
            ADOCommentProperty.SUPPORTS_MARKDOWN: ADOCommentProperty.create_bool(True),
        }

        if comment_identifier:
            properties[ADOCommentProperty.COMMENT_IDENTIFIER] = ADOCommentProperty.create_string(
                comment_identifier
            )

        body = {
            "comments": comments,
            "properties": properties,
            "status": (status.value if status is not None else ADOCommentStatus.ACTIVE.value),
        }

        if thread_location is not None:
            body["threadContext"] = thread_location.generate_representation()

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    def delete_thread(self, thread: ADOThread) -> None:
        """Delete a comment thread from a pull request.

        :param thread: The thread to delete
        """

        thread_id = thread["id"]

        self.log.debug(f"Deleting thread: ({self.pull_request_id}) {thread_id}")

        for comment in thread["comments"]:
            comment_id = comment["id"]
            self.log.debug(f"Deleting comment: {comment_id}")
            request_url = self.http_client.api_endpoint(project_id=self.project_id)
            request_url += f"/git/repositories/{self.repository_id}"
            request_url += f"/pullRequests/{self.pull_request_id}/threads/{thread_id}"
            request_url += f"/comments/{comment_id}?api-version=3.0-preview"
            requests.delete(
                request_url,
                headers=self.http_client.construct_headers(),
            )

    def create_thread_list(
        self,
        *,
        threads: list[ADOComment],
        comment_identifier: str | None = None,
    ) -> None:
        """Create a list of threads

        :param threads: The threads to create
        :param comment_identifier: A unique identifier for the comments that can be used for
                                                 identification at a later date

        :raises ADOException: If a thread is not an ADO comment
        """

        self.log.debug(f"Setting threads on PR: {self.pull_request_id}")

        # Check the type of the input
        for thread in threads:
            if not isinstance(thread, ADOComment):
                raise ADOException("Thread was not an ADOComment: " + str(thread))

        for thread in threads:
            self.log.debug("Adding thread")
            self.create_comment(thread, comment_identifier=comment_identifier)

    def get_statuses(self) -> ADOResponse:
        """Get the statuses on a PR.

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting PR statuses on PR {self.pull_request_id}")

        request_url = (
            self.http_client.api_endpoint(project_id=self.project_id)
            + f"/git/repositories/{self.repository_id}"
            + f"/pullRequests/{self.pull_request_id}/statuses?api-version=6.0-preview.1"
        )

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def set_status(
        self,
        state: ADOGitStatusState,
        identifier: str,
        description: str,
        context: str,
        *,
        iteration: int | None = None,
        target_url: str | None = None,
    ) -> ADOResponse:
        """Set a status on a PR.

        :param state: The state to set the status to.
        :param identifier: A unique identifier for the status (so it can be changed later)
        :param description: The text to show in the status
        :param context: The context for the build status
        :param iteration: The iteration of the PR to set the status on
        :param target_url: An optional URL to set which is opened when the description is clicked.

        :returns: The ADO response with the data in it
        """

        self.log.debug(
            f"Setting PR status ({state}) on PR ({self.pull_request_id}): {identifier} -> {description}"
        )

        request_url = (
            self.http_client.api_endpoint(project_id=self.project_id)
            + f"/git/repositories/{self.repository_id}"
            + f"/pullRequests/{self.pull_request_id}/statuses?api-version=4.0-preview"
        )

        body: dict[str, Any] = {
            "state": state.value,
            "description": description,
            "context": {"name": context, "genre": identifier},
        }

        if iteration is not None:
            body["iterationId"] = iteration

        if target_url is not None:
            body["targetUrl"] = target_url

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    def _thread_matches_identifier(self, thread: ADOThread, identifier: str) -> bool:
        """Check if the ADO thread matches the user and identifier

        :param thread: The thread to check
        :param identifier: The identifier to check against

        :returns: True if the thread matches, False otherwise

        :raises ADOException: If we couldn't find the author or the properties
        """

        _ = self

        try:
            # Deleted threads can stay around if they have other comments, so we
            # check if it was deleted before we check anything else.
            if thread["comments"][0]["isDeleted"]:
                return False
        except Exception:
            # If it's not there, it's not set
            pass

        try:
            properties = thread["properties"]
        except Exception as ex:
            raise ADOException("Could not find properties in thread: " + str(thread)) from ex

        if properties is None:
            return False

        comment_identifier = properties.get(ADOCommentProperty.COMMENT_IDENTIFIER)

        if comment_identifier is None:
            return False

        value = comment_identifier.get("$value")

        if value == identifier:
            return True

        return False

    def threads_with_identifier(self, identifier: str) -> list[ADOThread]:
        """Get the threads on a PR which begin with the prefix specified.

        :param identifier: The identifier to look for threads with

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

        :param identifier: The identifier property value to look for threads matching
        """

        self.log.debug(
            f'Deleting threads with identifier "{identifier}" on PR {self.pull_request_id}'
        )

        for thread in self.threads_with_identifier(identifier):
            self.log.debug(f"Deleting thread: {thread}")
            self.delete_thread(thread=thread)

    def get_properties(self) -> dict[str, PropertyValue]:
        """Get the properties on the PR from ADO.

        :returns: The properties that were found
        """

        self.log.debug(f"Getting properties: {self.pull_request_id}")
        request_url = (
            self.http_client.api_endpoint(project_id=self.project_id)
            + f"/git/repositories/{self.repository_id}"
            + f"/pullRequests/{self.pull_request_id}/properties?api-version=5.1-preview.1"
        )
        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        raw_properties = self.http_client.extract_value(response_data)

        properties = deserialize.deserialize(dict[str, PropertyValue], raw_properties)

        return properties

    def patch_properties(self, operations: list[PatchOperation]) -> dict[str, PropertyValue]:
        """Patch the properties on the PR.

        Usually add_property(), delete_property() and update_property() are
        going to be what you need instead of this base function.

        :param operations: The raw operations

        :returns: The new properties
        """

        self.log.debug(f"Patching properties: {self.pull_request_id}")
        request_url = (
            self.http_client.api_endpoint(project_id=self.project_id)
            + f"/git/repositories/{self.repository_id}"
            + f"/pullRequests/{self.pull_request_id}/properties?api-version=5.1-preview.1"
        )

        response = self.http_client.patch(request_url, operations=operations)

        response_data = self.http_client.decode_response(response)
        raw_properties = self.http_client.extract_value(response_data)

        properties = deserialize.deserialize(dict[str, PropertyValue], raw_properties)

        return properties

    def add_property(self, name: str, value: str) -> dict[str, PropertyValue]:
        """Add a property to the PR.

        :param name: The name of the property to add
        :param value: The value of the property to add

        :returns: The new properties
        """

        operation = AddOperation("/" + name, value)
        return self.patch_properties([operation])

    def delete_property(self, name: str) -> dict[str, PropertyValue]:
        """Delete a property from the PR.

        :param name: The name of the property to delete

        :returns: The new properties
        """

        operation = DeleteOperation("/" + name)
        return self.patch_properties([operation])
