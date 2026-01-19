#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO work items API wrapper."""

import logging
import os
import typing
from typing import Any, cast, Iterator, List, TypeVar

from simple_ado.base_client import ADOBaseClient
from simple_ado.exceptions import ADOException, ADOHTTPException
from simple_ado.http_client import ADOHTTPClient, ADOResponse
from simple_ado.utilities import boolstr

from simple_ado.models import (
    PatchOperation,
    AddOperation,
    WorkItemRelationType,
    ADOWorkItemBuiltInFields,
)
from simple_ado.work_item import ADOWorkItem


class BatchRequest:
    """The base type for a batch request.

    :param method: The HTTP method to use for the batch request
    :param uri: The URI for the batch request
    :param headers: The headers to be sent with the batch request
    """

    method: str
    uri: str
    headers: dict[str, str]

    def __init__(self, method: str, uri: str, headers: dict[str, str]) -> None:
        self.method = method
        self.uri = uri
        self.headers = headers

    def body(self) -> dict[str, Any]:
        """Generate the body of the request to be used in the API call.

        :returns: A dictionary with the raw API data for the request
        """
        return {"method": self.method, "uri": self.uri, "headers": self.headers}


class DeleteBatchRequest(BatchRequest):
    """A deletion batch request.

    :param uri: The URI for the batch request
    :param headers: The headers to be sent with the batch request
    """

    def __init__(self, uri: str, headers: dict[str, str] | None = None) -> None:
        if headers is None:
            headers = {}

        if headers.get("Content-Type") is None:
            headers["Content-Type"] = "application/json-patch+json"

        super().__init__("DELETE", uri, headers)


class ADOWorkItemsClient(ADOBaseClient):
    """Wrapper class around the ADO work items APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("workitems"))

    # TODO: Switch this to the default on next major version bump
    def get(self, identifier: str, project_id: str) -> ADOResponse:
        """Get the data about a work item.

        :param identifier: The identifier of the work item
        :param project_id: The ID of the project

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting work item: {identifier}")
        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/wit/workitems/{identifier}?api-version=4.1&$expand=all"
        )
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def get_work_item(self, identifier: str, project_id: str) -> ADOWorkItem:
        """Get a work item as an ADOWorkItem object.

        :param identifier: The identifier of the work item
        :param project_id: The ID of the project

        :returns: An ADOWorkItem object wrapping the work item data
        """

        self.log.debug(f"Getting work item: {identifier}")
        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/wit/workitems/{identifier}?api-version=4.1&$expand=all"
        )
        response = self.http_client.get(request_url)
        data = self.http_client.decode_response(response)
        return ADOWorkItem(data, self, project_id, self.log)

    # TODO: Switch this to the default on next major version bump
    def list(self, identifiers: List[int], project_id: str) -> ADOResponse:
        """Get a list of work items.

        :param identifiers: The list of requested work item ids
        :param project_id: The ID of the project

        :returns: The ADO response with the data in it
        """

        ids = ",".join(map(str, identifiers))

        self.log.debug(f"Getting work items: {ids}")
        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/wit/workitems?api-version=4.1&ids={ids}&$expand=all"
        )
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    # TODO: Switch this to the default on next major version bump
    def ilist(self, identifiers: List[int], project_id: str) -> Iterator[dict[str, Any]]:
        """Get a list of work items.

        :param identifiers: The list of requested work item ids
        :param project_id: The ID of the project

        :returns: The ADO response with the data in it
        """

        T = TypeVar("T")

        # batched is only available in Python 3.12+
        def batched(sequence: List[T], n: int) -> Iterator[List[T]]:
            """Batch data into lists of length n.

            :param sequence: The iterable to batch
            :param n: The batch size

            :returns: An iterator of lists of size n
            """
            for i in range(0, len(sequence), n):
                yield sequence[i : i + n]

        for id_chunk in batched(identifiers, 200):

            ids = ",".join(map(str, id_chunk))

            self.log.debug(f"Getting work items: {ids}")
            request_url = (
                self.http_client.api_endpoint(project_id=project_id)
                + f"/wit/workitems?api-version=4.1&ids={ids}&$expand=all"
            )
            response = self.http_client.get(request_url)
            data = self.http_client.decode_response(response)

            yield from data.get("value", [])

    def list_work_items(self, identifiers: List[int], project_id: str) -> Iterator[ADOWorkItem]:
        """Get a list of work items as ADOWorkItem objects with automatic chunking.

        :param identifiers: The list of requested work item ids
        :param project_id: The ID of the project

        :returns: An iterator of ADOWorkItem objects
        """

        T = TypeVar("T")

        # batched is only available in Python 3.12+
        def batched(sequence: List[T], n: int) -> Iterator[List[T]]:
            """Batch data into lists of length n.

            :param sequence: The iterable to batch
            :param n: The batch size

            :returns: An iterator of lists of size n
            """
            for i in range(0, len(sequence), n):
                yield sequence[i : i + n]

        for id_chunk in batched(identifiers, 200):

            ids = ",".join(map(str, id_chunk))

            self.log.debug(f"Getting work items: {ids}")
            request_url = (
                self.http_client.api_endpoint(project_id=project_id)
                + f"/wit/workitems?api-version=4.1&ids={ids}&$expand=all"
            )
            response = self.http_client.get(request_url)
            data = self.http_client.decode_response(response)

            for item_data in data.get("value", []):
                yield ADOWorkItem(item_data, self, project_id, self.log)

    def get_work_item_types(self, project_id: str) -> ADOResponse:
        """Get the types of work items supported by the project.

        :returns: The ADO response with the data in it
        """
        self.log.debug("Getting work item types")
        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/wit/workitemtypes?api-version=4.1"
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def add_property(
        self,
        *,
        identifier: str,
        field: str | ADOWorkItemBuiltInFields,
        value: str,
        project_id: str,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Add a property value to a work item.

        :param identifier: The identifier of the work item
        :param field: The field to add (either a string or ADOWorkItemBuiltInFields enum)
        :param value: The value to set the field to
        :param project_id: The ID of the project
        :param bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """

        # Convert enum to string value if needed
        field_str = field.value if isinstance(field, ADOWorkItemBuiltInFields) else field

        # Add /fields/ prefix if not already present (and not a special path like /relations/)
        if not field_str.startswith("/"):
            field_str = f"/fields/{field_str}"

        self.log.debug(f"Add field '{field_str}' to ticket {identifier}")

        operation = AddOperation(field_str, value)

        request_url = (
            f"{self.http_client.api_endpoint(project_id=project_id)}/wit/workitems/{identifier}"
        )
        request_url += f"?bypassRules={boolstr(bypass_rules)}"
        request_url += f"&suppressNotifications={boolstr(supress_notifications)}"
        request_url += "&api-version=4.1"

        response = self.http_client.patch(
            request_url,
            operations=[operation],
            additional_headers={"Content-Type": "application/json-patch+json"},
        )

        return self.http_client.decode_response(response)

    def add_attachment(
        self,
        *,
        identifier: str,
        path_to_attachment: str,
        project_id: str,
        filename: str | None = None,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Add an attachment to a work item.

        :param identifier: The identifier of the work item
        :param path_to_attachment: The path to the attachment on disk
        :param project_id: The ID of the project
        :param filename: The new file name of the attachment
        :param bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it

        :raises ADOException: If we can't get the url from the response
        """

        self.log.debug(f"Adding attachment to {identifier}: {path_to_attachment}")

        if filename is None:
            filename = os.path.basename(path_to_attachment)

        filename = filename.replace("#", "_")

        # Upload the file
        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/wit/attachments?fileName={filename}&api-version=1.0"
        )

        response = self.http_client.post_file(request_url, path_to_attachment)

        response_data = self.http_client.decode_response(response)

        url = response_data.get("url")

        if url is None:
            raise ADOException(f"Failed to get url from response: {response_data}")

        # Attach it to the ticket
        operation = AddOperation(
            "/relations/-",
            {"rel": "AttachedFile", "url": url, "attributes": {"comment": ""}},
        )

        request_url = (
            f"{self.http_client.api_endpoint(project_id=project_id)}/wit/workitems/{identifier}"
        )
        request_url += f"?bypassRules={boolstr(bypass_rules)}"
        request_url += f"&suppressNotifications={boolstr(supress_notifications)}"
        request_url += "&api-version=4.1"

        response = self.http_client.patch(
            request_url,
            operations=[operation],
            additional_headers={"Content-Type": "application/json-patch+json"},
        )

        return self.http_client.decode_response(response)

    def _add_link(
        self,
        *,
        parent_identifier: str,
        child_url: str,
        relation_type: WorkItemRelationType,
        project_id: str,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Add a link between a parent work item and another resource.

        :param parent_identifier: The identifier of the parent work item
        :param child_url: The URL of the child item to link to
        :param relation_type: The relationship type between
                                                   the parent and the child
        :param project_id: The ID of the project
        :param bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Adding link {parent_identifier} -> {child_url} ({relation_type})")

        operation = AddOperation(
            "/relations/-",
            {
                "rel": relation_type.value,
                "url": child_url,
                "attributes": {"comment": ""},
            },
        )

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/wit/workitems/{parent_identifier}"
        request_url += f"?bypassRules={boolstr(bypass_rules)}"
        request_url += f"&suppressNotifications={boolstr(supress_notifications)}"
        request_url += "&api-version=4.1"

        response = self.http_client.patch(
            request_url,
            operations=[operation],
            additional_headers={"Content-Type": "application/json-patch+json"},
        )

        return self.http_client.decode_response(response)

    def link_tickets(
        self,
        *,
        parent_identifier: str,
        child_identifier: str,
        relationship: WorkItemRelationType,
        project_id: str,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Add a link between a parent and child work item.

        :param parent_identifier: The identifier of the parent work item
        :param child_identifier: The identifier of the child work item
        :param relationship: The relationship type between
                                                  the two work items
        :param project_id: The ID of the project
        :param bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """
        child_url = f"{self.http_client.api_endpoint()}/wit/workitems/{child_identifier}"
        return self._add_link(
            parent_identifier=parent_identifier,
            child_url=child_url,
            relation_type=relationship,
            project_id=project_id,
            bypass_rules=bypass_rules,
            supress_notifications=supress_notifications,
        )

    def add_hyperlink(
        self,
        *,
        identifier: str,
        hyperlink: str,
        project_id: str,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Add a hyperlink link to a work item.

        :param identifier: The identifier of the work item
        :param hyperlink: The hyperlink to add to the work item
        :param project_id: The ID of the project
        :param bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """
        return self._add_link(
            parent_identifier=identifier,
            child_url=hyperlink,
            relation_type=WorkItemRelationType.HYPERLINK,
            project_id=project_id,
            bypass_rules=bypass_rules,
            supress_notifications=supress_notifications,
        )

    def create(
        self,
        *,
        item_type: str,
        operations: List[AddOperation],
        project_id: str,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Create a new work item.

        :param item_type: The type of work item to create
        :param operations: The list of add operations to use to create the
                           ticket
        :param project_id: The ID of the project
        :param bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Creating a new {item_type}")

        request_url = (
            f"{self.http_client.api_endpoint(project_id=project_id)}/wit/workitems/${item_type}"
        )
        request_url += f"?bypassRules={boolstr(bypass_rules)}"
        request_url += f"&suppressNotifications={boolstr(supress_notifications)}"
        request_url += "&api-version=4.1"

        response = self.http_client.post(
            request_url,
            operations=cast(List[PatchOperation], operations),
            additional_headers={"Content-Type": "application/json-patch+json"},
        )

        return self.http_client.decode_response(response)

    def update(
        self,
        *,
        identifier: str,
        operations: List[PatchOperation],
        project_id: str,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Update a work item.

        :param identifier: The identifier of the work item
        :param operations: The list of operations to use to update the ticket
        :param project_id: The ID of the project
        :param bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Updating {identifier}")

        request_url = (
            f"{self.http_client.api_endpoint(project_id=project_id)}/wit/workitems/{identifier}"
        )
        request_url += f"?bypassRules={boolstr(bypass_rules)}"
        request_url += f"&suppressNotifications={boolstr(supress_notifications)}"
        request_url += "&api-version=4.1"

        response = self.http_client.patch(
            request_url,
            operations=operations,
            additional_headers={"Content-Type": "application/json-patch+json"},
        )

        return self.http_client.decode_response(response)

    def execute_query(self, query_string: str, project_id: str) -> ADOResponse:
        """Execute a WIQL query.

        :param query_string: The WIQL query string to execute
        :param project_id: The ID of the project

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Executing query: {query_string}")

        request_url = (
            f"{self.http_client.api_endpoint(project_id=project_id)}/wit/wiql?api-version=4.1"
        )

        response = self.http_client.post(request_url, json_data={"query": query_string})

        return self.http_client.decode_response(response)

    def execute_query_by_id(self, query_id: str, project_id: str) -> ADOResponse:
        """Gets the results of the query given the query ID.

        :param query_id: The query id to execute
        :param project_id: The ID of the project

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Executing query with id: {query_id}")

        request_url = f"{self.http_client.api_endpoint(project_id=project_id)}/wit/wiql/{query_id}?api-version=4.1"

        response = self.http_client.get(request_url)

        return self.http_client.decode_response(response)

    def delete(
        self,
        *,
        identifier: str,
        project_id: str,
        permanent: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Delete a work item.

        :param identifier: The identifier of the work item
        :param project_id: The ID of the project
        :param permanent: Set to True if we should permanently delete the
                               work item, False otherwise
        :param supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it

        :raises ADOHTTPException: Raised if the response code is not 204 (No Content)
        """

        self.log.debug(f"Deleting {identifier}")

        request_url = (
            f"{self.http_client.api_endpoint(project_id=project_id)}/wit/workitems/{identifier}"
        )
        request_url += f"?suppressNotifications={boolstr(supress_notifications)}"
        request_url += f"&destroy={boolstr(permanent)}"
        request_url += "&api-version=4.1"

        response = self.http_client.delete(
            request_url,
            additional_headers={"Content-Type": "application/json-patch+json"},
        )

        if response.status_code != 204:
            raise ADOHTTPException(f"Failed to delete '{identifier}'", response)

        return self.http_client.decode_response(response)

    def batch(self, operations: typing.List[BatchRequest]) -> ADOResponse:
        """Run a batch operation.

        :param operations: The list of batch operations to run

        :returns: The ADO response with the data in it

        :raises ADOException: Raised if we try and run more than 200 batch operations at once
        """

        if len(operations) >= 200:
            raise ADOException("Cannot perform more than 200 batch operations at once")

        self.log.debug("Running batch operation")

        full_body: list[dict[str, Any]] = []
        for operation in operations:
            full_body.append(operation.body())

        request_url = f"{self.http_client.api_endpoint()}/wit/$batch"

        response = self.http_client.post(request_url, json_data=full_body)

        return self.http_client.decode_response(response)
