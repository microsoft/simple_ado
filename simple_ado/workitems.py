#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO work items API wrapper."""

import datetime
import enum
import logging
import os
from typing import Any, Dict, List, Optional, Union

from simple_ado.base_client import ADOBaseClient
from simple_ado.context import ADOContext
from simple_ado.exceptions import ADOException, ADOHTTPException
from simple_ado.http_client import ADOHTTPClient, ADOResponse


class BatchRequest:
    """The base type for a batch request.

    :param method: The HTTP method to use for the batch request
    :param uri: The URI for the batch request
    :param headers: The headers to be sent with the batch request
    """

    method: str
    uri: str
    headers: Dict[str, str]

    def __init__(self, method: str, uri: str, headers: Dict[str, str]) -> None:
        self.method = method
        self.uri = uri
        self.headers = headers

    def body(self) -> Dict[str, Any]:
        """Generate the body of the request to be used in the API call.

        :returns: A dictionary with the raw API data for the request
        """
        return {"method": self.method, "uri": self.uri, "headers": self.headers}


class DeleteBatchRequest(BatchRequest):
    """A deletion batch request.

    :param uri: The URI for the batch request
    :param headers: The headers to be sent with the batch request
    """

    def __init__(self, uri: str, headers: Optional[Dict[str, str]] = None) -> None:
        if headers is None:
            headers = {}

        if headers.get("Content-Type") is None:
            headers["Content-Type"] = "application/json-patch+json"

        super().__init__("DELETE", uri, headers)


class WorkItemRelationType(enum.Enum):
    """Defines the various relationship types between work items."""

    produces_for = "System.LinkTypes.Remote.Dependency-Forward"
    consumes_from = "System.LinkTypes.Remote.Dependency-Reverse"

    duplicate = "System.LinkTypes.Duplicate-Forward"
    duplicate_of = "System.LinkTypes.Duplicate-Reverse"

    blocked_by = "Microsoft.VSTS.BlockingLink-Forward"
    blocking = "Microsoft.VSTS.BlockingLink-Reverse"

    referenced_by = "Microsoft.VSTS.TestCase.SharedParameterReferencedBy-Forward"
    references = "Microsoft.VSTS.TestCase.SharedParameterReferencedBy-Reverse"

    tested_by = "Microsoft.VSTS.Common.TestedBy-Forward"
    tests = "Microsoft.VSTS.Common.TestedBy-Reverse"

    test_case = "Microsoft.VSTS.TestCase.SharedStepReferencedBy-Forward"
    shared_steps = "Microsoft.VSTS.TestCase.SharedStepReferencedBy-Reverse"

    successor = "System.LinkTypes.Dependency-Forward"
    predecessor = "System.LinkTypes.Dependency-Reverse"

    child = "System.LinkTypes.Hierarchy-Forward"
    parent = "System.LinkTypes.Hierarchy-Reverse"

    remote_related = "System.LinkTypes.Remote.Related"
    related = "System.LinkTypes.Related"

    attached_file = "AttachedFile"

    hyperlink = "Hyperlink"

    artifact_link = "ArtifactLink"


class WorkItemField(enum.Enum):
    """Defines the various fields available on a work item.

    This does not include custom fields.
    """

    area_path = "/fields/System.AreaPath"
    assigned_to = "/fields/System.AssignedTo"
    changed_date = "/fields/System.ChangedDate"
    closed_date = "/fields/Microsoft.VSTS.Common.ClosedDate"
    created_by = "/fields/System.CreatedBy"
    created_date = "/fields/System.CreatedDate"
    description = "/fields/System.Description"
    duplicate_id = "/fields/Office.Common.DuplicateID"
    history = "/fields/System.History"
    priority = "/fields/Microsoft.VSTS.Common.Priority"
    resolved_date = "/fields/Microsoft.VSTS.Common.ResolvedDate"
    resolved_reason = "/fields/Microsoft.VSTS.Common.ResolvedReason"
    state = "/fields/System.State"
    substatus = "/fields/Office.Common.SubStatus"
    tags = "/fields/System.Tags"
    title = "/fields/System.Title"

    relation = "/relations/-"


class WorkItemFieldOperationType(enum.Enum):
    """Define the field operation types."""

    add = "add"
    copy = "copy"
    move = "move"
    remove = "remove"
    replace = "replace"
    test = "test"


class WorkItemFieldOperation:
    """Defines a base patch operation for sending via the ADO API.

    :param operation: The operation type
    :param path: The path to apply the operation to
    :param value: The value (if any) to use
    :param from_path: The original path (if required)
    """

    def __init__(
        self,
        operation: WorkItemFieldOperationType,
        path: Union[WorkItemField, str],
        value: Optional[str],
        from_path: Optional[str] = None,
    ) -> None:
        self.operation = operation
        self.path = path
        self.value = value
        self.from_path = from_path

    def raw(self) -> Dict[str, Any]:
        """Generate the raw representation that is sent to the API.

        :returns: A dictionary with the raw API data for the request
        """

        if isinstance(self.value, datetime.datetime):
            self.value = (
                self.value.strftime("%Y-%m-%dT%H:%M:%S.")
                + str(int(self.value.microsecond / 10000))
                + "Z"
            )

        if isinstance(self.value, enum.Enum):
            self.value = self.value.value

        raw_dict = {"op": self.operation.value, "value": self.value, "from": self.from_path}

        if isinstance(self.path, str):
            raw_dict["path"] = self.path
        else:
            raw_dict["path"] = self.path.value

        return raw_dict

    def __str__(self) -> str:
        """Generate and return the string representation of the object.

        :return: A string representation of the object
        """
        return str(self.raw())


class WorkItemFieldOperationAdd(WorkItemFieldOperation):
    """Defines an add operation for sending via the ADO API.

    :param field: The field to add
    :param value: The value to set for the new field
    """

    def __init__(self, field: WorkItemField, value: Any) -> None:
        super().__init__(WorkItemFieldOperationType.add, field, value)


class WorkItemFieldOperationDelete(WorkItemFieldOperation):
    """Defines a delete operation for sending via the ADO API.

    :param field: The field to delete
    """

    def __init__(self, field: WorkItemField) -> None:
        super().__init__(WorkItemFieldOperationType.remove, field, None)


class ADOWorkItemsClient(ADOBaseClient):
    """Wrapper class around the ADO work items APIs.

    :param context: The context information for the client
    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(
        self, context: ADOContext, http_client: ADOHTTPClient, log: logging.Logger
    ) -> None:
        super().__init__(context, http_client, log.getChild("workitems"))

    def get(self, identifier: str) -> ADOResponse:
        """Get the data about a work item.

        :param identifier: The identifier of the work item

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Getting work item: {identifier}")
        request_url = (
            f"{self._http_client.base_url()}/wit/workitems/{identifier}?api-version=4.1&$expand=all"
        )
        response = self._http_client.get(request_url)
        return self._http_client.decode_response(response)

    def get_work_item_types(self) -> ADOResponse:
        """Get the types of work items supported by the project.

        :returns: The ADO response with the data in it
        """
        self.log.debug("Getting work item types")
        request_url = f"{self._http_client.base_url()}/wit/workitemtypes?api-version=4.1"
        response = self._http_client.get(request_url)
        return self._http_client.decode_response(response)

    def add_property(
        self,
        identifier: str,
        field: WorkItemField,
        value: Any,
        *,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Add a property value to a work item.

        :param identifier: The identifier of the work item
        :param field: The field to add
        :param value: The value to set the field to
        :param bool bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param bool supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Add field '{field.value}' to ticket {identifier}")

        operation = WorkItemFieldOperationAdd(field, value)

        request_url = f"{self._http_client.base_url()}/wit/workitems/{identifier}"
        request_url += f"?bypassRules={bypass_rules}"
        request_url += f"&suppressNotifications={supress_notifications}"
        request_url += f"&api-version=4.1"

        response = self.http_client.patch(
            request_url,
            [operation.raw()],
            additional_headers={"Content-Type": "application/json-patch+json"},
        )

        return self._http_client.decode_response(response)

    def add_attachment(
        self,
        identifier: str,
        path_to_attachment: str,
        *,
        filename: Optional[str] = None,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Add an attachment to a work item.

        :param identifier: The identifier of the work item
        :param path_to_attachment: The path to the attachment on disk
        :param Optional[str] filename: The new file name of the attachment
        :param bool bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param bool supress_notifications: Set to True if notifications for this
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
            f"{self._http_client.base_url()}/wit/attachments?fileName={filename}&api-version=1.0"
        )

        response = self.http_client.post_file(request_url, path_to_attachment)

        response_data = self._http_client.decode_response(response)

        url = response_data.get("url")

        if url is None:
            raise ADOException(f"Failed to get url from response: {response_data}")

        # Attach it to the ticket
        operation = WorkItemFieldOperationAdd(
            WorkItemField.relation,
            {"rel": "AttachedFile", "url": url, "attributes": {"comment": ""}},
        )

        request_url = f"{self._http_client.base_url()}/wit/workitems/{identifier}"
        request_url += f"?bypassRules={bypass_rules}"
        request_url += f"&suppressNotifications={supress_notifications}"
        request_url += f"&api-version=4.1"

        response = self.http_client.patch(
            request_url,
            [operation.raw()],
            additional_headers={"Content-Type": "application/json-patch+json"},
        )

        return self._http_client.decode_response(response)

    def _add_link(
        self,
        *,
        parent_identifier: str,
        child_url: str,
        relation_type: WorkItemRelationType,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Add a link between a parent work item and another resource.

        :param str parent_identifier: The identifier of the parent work item
        :param str child_url: The URL of the child item to link to
        :param WorkItemRelationType relation_type: The relationship type between
                                                   the parent and the child
        :param bool bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param bool supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Adding link {parent_identifier} -> {child_url} ({relation_type})")

        operation = WorkItemFieldOperationAdd(
            WorkItemField.relation,
            {"rel": relation_type.value, "url": child_url, "attributes": {"comment": ""}},
        )

        request_url = f"{self._http_client.base_url()}/wit/workitems/{parent_identifier}"
        request_url += f"?bypassRules={bypass_rules}"
        request_url += f"&suppressNotifications={supress_notifications}"
        request_url += f"&api-version=4.1"

        response = self.http_client.patch(
            request_url,
            [operation.raw()],
            additional_headers={"Content-Type": "application/json-patch+json"},
        )

        return self._http_client.decode_response(response)

    def link_tickets(
        self,
        parent_identifier: str,
        child_identifier: str,
        relationship: WorkItemRelationType,
        *,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Add a link between a parent and child work item.

        :param parent_identifier: The identifier of the parent work item
        :param child_identifier: The identifier of the child work item
        :param WorkItemRelationType relationship: The relationship type between
                                                  the two work items
        :param bool bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param bool supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """
        child_url = (
            f"{self._http_client.base_url(is_project=False)}/wit/workitems/{child_identifier}"
        )
        return self._add_link(
            parent_identifier=parent_identifier,
            child_url=child_url,
            relation_type=relationship,
            bypass_rules=bypass_rules,
            supress_notifications=supress_notifications,
        )

    def add_hyperlink(
        self,
        identifier: str,
        hyperlink: str,
        *,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Add a hyperlink link to a work item.

        :param identifier: The identifier of the work item
        :param hyperlink: The hyperlink to add to the work item
        :param bool bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param bool supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """
        return self._add_link(
            parent_identifier=identifier,
            child_url=hyperlink,
            relation_type=WorkItemRelationType.hyperlink,
            bypass_rules=bypass_rules,
            supress_notifications=supress_notifications,
        )

    def create(
        self,
        item_type: str,
        operations: List[WorkItemFieldOperationAdd],
        *,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Create a new work item.

        :param item_type: The type of work item to create
        :param operations: The list of add operations to use to create the
                           ticket
        :param bool bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param bool supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Creating a new {item_type}")

        request_url = f"{self._http_client.base_url()}/wit/workitems/${item_type}"
        request_url += f"?bypassRules={bypass_rules}"
        request_url += f"&suppressNotifications={supress_notifications}"
        request_url += f"&api-version=4.1"

        response = self.http_client.post(
            request_url,
            [operation.raw() for operation in operations],
            additional_headers={"Content-Type": "application/json-patch+json"},
        )

        return self._http_client.decode_response(response)

    def update(
        self,
        identifier: str,
        operations: List[WorkItemFieldOperation],
        *,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> ADOResponse:
        """Update a work item.

        :param identifier: The identifier of the work item
        :param operations: The list of operations to use to update the ticket
        :param bool bypass_rules: Set to True if we should bypass validation
                                  rules, False otherwise
        :param bool supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Updating {identifier}")

        request_url = f"{self._http_client.base_url()}/wit/workitems/{identifier}"
        request_url += f"?bypassRules={bypass_rules}"
        request_url += f"&suppressNotifications={supress_notifications}"
        request_url += f"&api-version=4.1"

        response = self.http_client.patch(
            request_url,
            [operation.raw() for operation in operations],
            additional_headers={"Content-Type": "application/json-patch+json"},
        )

        return self._http_client.decode_response(response)

    def execute_query(self, query_string: str) -> ADOResponse:
        """Execute a WIQL query.

        :param query_string: The WIQL query string to execute

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Executing query: {query_string}")

        request_url = f"{self._http_client.base_url()}/wit/wiql?api-version=4.1"

        response = self.http_client.post(request_url, {"query": query_string})

        return self._http_client.decode_response(response)

    def delete(
        self, identifier: str, *, permanent: bool = False, supress_notifications: bool = False
    ) -> ADOResponse:
        """Delete a work item.

        :param identifier: The identifier of the work item
        :param bool permanent: Set to True if we should permanently delete the
                               work item, False otherwise
        :param bool supress_notifications: Set to True if notifications for this
                                           change should be supressed, False
                                           otherwise

        :returns: The ADO response with the data in it

        :raises ADOHTTPException: Raised if the response code is not 204 (No Content)
        """

        self.log.debug(f"Deleting {identifier}")

        request_url = f"{self._http_client.base_url()}/wit/workitems/{identifier}"
        request_url += f"?suppressNotifications={supress_notifications}"
        request_url += f"&destroy={str(permanent).lower()}"
        request_url += f"&api-version=4.1"

        response = self.http_client.delete(
            request_url, additional_headers={"Content-Type": "application/json-patch+json"}
        )

        if response.status_code != 204:
            raise ADOHTTPException(
                f"Failed to delete '{identifier}'", response.status_code, response.text
            )

        return self._http_client.decode_response(response)

    def batch(self, operations: List[BatchRequest]) -> ADOResponse:
        """Run a batch operation.

        :param operations: The list of batch operations to run

        :returns: The ADO response with the data in it

        :raises ADOException: Raised if we try and run more than 200 batch operations at once
        """

        if len(operations) >= 200:
            raise ADOException("Cannot perform more than 200 batch operations at once")

        self.log.debug("Running batch operation")

        full_body = []
        for operation in operations:
            full_body.append(operation.body())

        request_url = f"{self._http_client.base_url(is_project=False)}/wit/$batch"

        response = self.http_client.post(request_url, full_body)

        return self._http_client.decode_response(response)
