"""Unit tests for ADOWorkItem class."""

import copy
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest
import responses
from simple_ado import ADOClient
from simple_ado.work_item import ADOWorkItem
from simple_ado.workitems import ADOWorkItemsClient
from simple_ado.models import ADOWorkItemBuiltInFields
from simple_ado.exceptions import ADOException


@pytest.fixture(name="mock_work_item_data")
def fixture_mock_work_item_data() -> dict[str, Any]:
    """Return mock work item data."""
    return {
        "id": 12345,
        "rev": 1,
        "fields": {
            "System.Title": "Test Work Item",
            "System.State": "Active",
            "System.AssignedTo": {"displayName": "Test User"},
            "System.WorkItemType": "Bug",
        },
        "url": "https://test.visualstudio.com/_apis/wit/workitems/12345",
    }


@pytest.fixture(name="mock_workitems_client")
def fixture_mock_workitems_client(mock_client: ADOClient) -> ADOWorkItemsClient:
    """Return a mock work items client."""
    return mock_client.workitems


def test_work_item_initialization(
    mock_work_item_data: dict[str, Any], mock_workitems_client: ADOWorkItemsClient
) -> None:
    """Test that ADOWorkItem initializes correctly."""
    work_item = ADOWorkItem(
        data=mock_work_item_data,
        client=mock_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    assert work_item.id == 12345
    assert work_item.data == mock_work_item_data


def test_work_item_getitem_string_key(
    mock_work_item_data: dict[str, Any], mock_workitems_client: ADOWorkItemsClient
) -> None:
    """Test accessing fields using string keys."""
    work_item = ADOWorkItem(
        data=mock_work_item_data,
        client=mock_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    assert work_item["System.Title"] == "Test Work Item"
    assert work_item["System.State"] == "Active"
    assert work_item["System.WorkItemType"] == "Bug"


def test_work_item_getitem_enum_key(
    mock_work_item_data: dict[str, Any], mock_workitems_client: ADOWorkItemsClient
) -> None:
    """Test accessing fields using ADOWorkItemBuiltInFields enum."""
    work_item = ADOWorkItem(
        data=mock_work_item_data,
        client=mock_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    assert work_item[ADOWorkItemBuiltInFields.TITLE] == "Test Work Item"
    assert work_item[ADOWorkItemBuiltInFields.STATE] == "Active"
    assert work_item[ADOWorkItemBuiltInFields.WORK_ITEM_TYPE] == "Bug"


def test_work_item_getitem_missing_field_raises(
    mock_work_item_data: dict[str, Any], mock_workitems_client: ADOWorkItemsClient
) -> None:
    """Test that accessing a non-existent field raises KeyError after refresh."""
    work_item = ADOWorkItem(
        data=mock_work_item_data,
        client=mock_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    # Mock the client's get method to return the same data (field still missing)
    mock_workitems_client.get = MagicMock(return_value=mock_work_item_data)  # type: ignore

    with pytest.raises(KeyError):
        _ = work_item["NonExistent.Field"]

    # Verify refresh was attempted
    mock_workitems_client.get.assert_called_once_with("12345", "test-project")


@responses.activate
def test_work_item_refresh(
    mock_work_item_data: dict[str, Any], mock_client: ADOClient, mock_project_id: str
) -> None:
    """Test refreshing work item data."""
    # Mock the API response
    updated_data = copy.deepcopy(mock_work_item_data)
    updated_data["fields"]["System.State"] = "Resolved"

    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
        json=updated_data,
        status=200,
    )

    work_item = ADOWorkItem(
        data=copy.deepcopy(mock_work_item_data),
        client=mock_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    # Initially Active
    assert work_item["System.State"] == "Active"

    # Refresh
    work_item.refresh()

    # Now should be Resolved
    assert work_item["System.State"] == "Resolved"


@responses.activate
def test_work_item_patch(
    mock_work_item_data: dict[str, Any], mock_client: ADOClient, mock_project_id: str
) -> None:
    """Test patching a work item field."""
    # Mock the API response
    updated_data = copy.deepcopy(mock_work_item_data)
    updated_data["fields"]["System.State"] = "Resolved"

    responses.add(
        responses.PATCH,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
        json=updated_data,
        status=200,
    )

    work_item = ADOWorkItem(
        data=copy.deepcopy(mock_work_item_data),
        client=mock_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    # Initially Active
    assert work_item["System.State"] == "Active"

    # Patch the state
    work_item.patch("System.State", "Resolved")

    # Should be updated
    assert work_item["System.State"] == "Resolved"


@responses.activate
def test_work_item_setitem(
    mock_work_item_data: dict[str, Any], mock_client: ADOClient, mock_project_id: str
) -> None:
    """Test setting a field using setitem."""
    # Mock the API response
    updated_data = copy.deepcopy(mock_work_item_data)
    updated_data["fields"]["System.Title"] = "New Title"

    responses.add(
        responses.PATCH,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
        json=updated_data,
        status=200,
    )

    work_item = ADOWorkItem(
        data=copy.deepcopy(mock_work_item_data),
        client=mock_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    # Set using item assignment
    work_item["System.Title"] = "New Title"

    # Should be updated
    assert work_item["System.Title"] == "New Title"


def test_work_item_repr(
    mock_work_item_data: dict[str, Any], mock_workitems_client: ADOWorkItemsClient
) -> None:
    """Test work item string representation."""
    work_item = ADOWorkItem(
        data=mock_work_item_data,
        client=mock_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    repr_str = repr(work_item)
    assert "ADOWorkItem" in repr_str
    assert "12345" in repr_str
    assert "Bug" in repr_str


def test_work_item_no_id_patch_raises(mock_workitems_client: ADOWorkItemsClient) -> None:
    """Test that patching without an ID raises an exception."""
    work_item_data = {"fields": {"System.Title": "Test"}}
    work_item = ADOWorkItem(
        data=work_item_data,
        client=mock_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    with pytest.raises(ADOException):
        work_item.patch("System.State", "Active")


def test_work_item_no_id_refresh_raises(mock_workitems_client: ADOWorkItemsClient) -> None:
    """Test that refreshing without an ID raises an exception."""
    work_item_data = {"fields": {"System.Title": "Test"}}
    work_item = ADOWorkItem(
        data=work_item_data,
        client=mock_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    with pytest.raises(ADOException):
        work_item.refresh()
