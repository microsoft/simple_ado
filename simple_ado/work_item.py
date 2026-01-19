#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO work item wrapper with lazy loading and patching capabilities."""

import logging
from typing import Any, TYPE_CHECKING

from simple_ado.exceptions import ADOException
from simple_ado.models import ADOWorkItemBuiltInFields, ReplaceOperation

if TYPE_CHECKING:
    from simple_ado.workitems import ADOWorkItemsClient


class ADOWorkItem:
    """Wrapper class for work item data with lazy loading and patching capabilities.

    :param data: The work item data from the API response
    :param client: The work items client for API operations
    :param project_id: The ID of the project this work item belongs to
    :param log: The logger to use
    """

    _data: dict[str, Any]
    _client: "ADOWorkItemsClient"
    _project_id: str
    _log: logging.Logger

    def __init__(
        self,
        data: dict[str, Any],
        client: "ADOWorkItemsClient",
        project_id: str,
        log: logging.Logger,
    ) -> None:
        """Initialize the work item wrapper.

        :param data: The work item data from the API response
        :param client: The work items client for API operations
        :param project_id: The ID of the project this work item belongs to
        :param log: The logger to use
        """
        self._data = data
        self._client = client
        self._project_id = project_id
        work_item_id = data.get("id", "unknown")
        self._log = log.getChild(f"workitem.{work_item_id}")

    @property
    def id(self) -> int | None:
        """Get the work item ID.

        :returns: The work item ID, or None if not present
        """
        return self._data.get("id")

    @property
    def data(self) -> dict[str, Any]:
        """Get the raw work item data.

        :returns: The complete work item data dictionary
        """
        return self._data

    def __getitem__(self, key: str | ADOWorkItemBuiltInFields) -> Any:
        """Get a field value from the work item.

        Supports both string field names and ADOWorkItemBuiltInFields enum values.
        If the field is not present in the current data, the work item will be
        refreshed from the server to try to populate missing fields.

        :param key: The field name or ADOWorkItemBuiltInFields enum value

        :returns: The field value

        :raises KeyError: If the field is not found even after refresh
        """
        # Convert enum to string value if needed
        field_name = key.value if isinstance(key, ADOWorkItemBuiltInFields) else key

        # Try to get from fields dict
        fields = self._data.get("fields", {})
        if field_name in fields:
            return fields[field_name]

        # Field not found, try refreshing from server
        self._log.debug(f"Field '{field_name}' not found, refreshing work item")
        self.refresh()

        # Try again after refresh
        fields = self._data.get("fields", {})
        if field_name in fields:
            return fields[field_name]

        # Still not found, raise KeyError
        raise KeyError(f"Field '{field_name}' not found in work item {self.id}")

    def __setitem__(self, key: str | ADOWorkItemBuiltInFields, value: Any) -> None:
        """Set a field value and patch it on the server.

        This is a convenience method that calls patch() internally.

        :param key: The field name or ADOWorkItemBuiltInFields enum value
        :param value: The new value for the field
        """
        self.patch(key, value)

    def refresh(self) -> None:
        """Refresh the work item data from the server.

        This reloads all fields from the API, which is useful for populating
        missing fields or getting the latest values.

        :raises ADOException: If the work item ID is not available
        """
        work_item_id = self.id
        if work_item_id is None:
            raise ADOException("Cannot refresh work item without an ID")

        self._log.debug(f"Refreshing work item {work_item_id}")
        self._data = self._client.get(str(work_item_id), self._project_id)

    def patch(
        self,
        field: str | ADOWorkItemBuiltInFields,
        value: Any,
        bypass_rules: bool = False,
        supress_notifications: bool = False,
    ) -> None:
        """Patch a field on the work item.

        This updates the field on the server and refreshes the local data.

        :param field: The field name or ADOWorkItemBuiltInFields enum value
        :param value: The new value for the field
        :param bypass_rules: Set to True if we should bypass validation rules
        :param supress_notifications: Set to True if notifications should be suppressed

        :raises ADOException: If the work item ID is not available
        """
        work_item_id = self.id
        if work_item_id is None:
            raise ADOException("Cannot patch work item without an ID")

        # We need the prefix to patch. If it's an enum, it gets handled further on
        if isinstance(field, str):
            field = f"/fields/{field}"

        self._log.debug(f"Patching field '{field}' on work item {work_item_id}")

        # Create replace operation
        operation = ReplaceOperation(field, value)

        # Call the client's update method
        response = self._client.update(
            identifier=str(work_item_id),
            operations=[operation],
            project_id=self._project_id,
            bypass_rules=bypass_rules,
            supress_notifications=supress_notifications,
        )

        # Update local data with response
        self._data = response

    def __repr__(self) -> str:
        """Get a string representation of the work item.

        :returns: A string representation showing the work item ID and type
        """
        work_item_id = self.id
        work_item_type = self._data.get("fields", {}).get("System.WorkItemType", "Unknown")
        return f"<ADOWorkItem(id={work_item_id}, type='{work_item_type}')>"
