"""Unit tests for the async ADOAsyncWorkItem class."""

import copy
import logging
from typing import Any

import httpx
import pytest
import respx
from simple_ado._async import ADOAsyncClient
from simple_ado._async.work_item import ADOAsyncWorkItem
from simple_ado._async.workitems import ADOAsyncWorkItemsClient
from simple_ado.models import ADOWorkItemBuiltInFields
from simple_ado.exceptions import ADOException


@pytest.fixture(name="mock_async_work_item_data")
def fixture_mock_async_work_item_data() -> dict[str, Any]:
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


@pytest.fixture(name="mock_async_workitems_client")
def fixture_mock_async_workitems_client(
    mock_async_client: ADOAsyncClient,
) -> ADOAsyncWorkItemsClient:
    """Return a mock async work items client."""
    return mock_async_client.workitems


@pytest.mark.asyncio
async def test_work_item_initialization(
    mock_async_work_item_data: dict[str, Any],
    mock_async_workitems_client: ADOAsyncWorkItemsClient,
) -> None:
    """Test that ADOAsyncWorkItem initializes correctly."""
    work_item = ADOAsyncWorkItem(
        data=mock_async_work_item_data,
        client=mock_async_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    assert work_item.id == 12345
    assert work_item.data == mock_async_work_item_data


@pytest.mark.asyncio
async def test_work_item_getitem_string_key(
    mock_async_work_item_data: dict[str, Any],
    mock_async_workitems_client: ADOAsyncWorkItemsClient,
) -> None:
    """Test accessing fields using string keys."""
    work_item = ADOAsyncWorkItem(
        data=mock_async_work_item_data,
        client=mock_async_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    assert work_item["System.Title"] == "Test Work Item"
    assert work_item["System.State"] == "Active"
    assert work_item["System.WorkItemType"] == "Bug"


@pytest.mark.asyncio
async def test_work_item_getitem_enum_key(
    mock_async_work_item_data: dict[str, Any],
    mock_async_workitems_client: ADOAsyncWorkItemsClient,
) -> None:
    """Test accessing fields using ADOWorkItemBuiltInFields enum."""
    work_item = ADOAsyncWorkItem(
        data=mock_async_work_item_data,
        client=mock_async_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    assert work_item[ADOWorkItemBuiltInFields.TITLE] == "Test Work Item"
    assert work_item[ADOWorkItemBuiltInFields.STATE] == "Active"
    assert work_item[ADOWorkItemBuiltInFields.WORK_ITEM_TYPE] == "Bug"


@pytest.mark.asyncio
async def test_work_item_getitem_missing_field_raises(
    mock_async_work_item_data: dict[str, Any],
    mock_async_workitems_client: ADOAsyncWorkItemsClient,
) -> None:
    """Test that accessing a non-existent field raises KeyError."""
    work_item = ADOAsyncWorkItem(
        data=mock_async_work_item_data,
        client=mock_async_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    with pytest.raises(KeyError):
        _ = work_item["NonExistent.Field"]


@pytest.mark.asyncio
@respx.mock
async def test_work_item_refresh(
    mock_async_work_item_data: dict[str, Any],
    mock_async_client: ADOAsyncClient,
    mock_project_id: str,
) -> None:
    """Test refreshing work item data."""
    updated_data = copy.deepcopy(mock_async_work_item_data)
    updated_data["fields"]["System.State"] = "Resolved"

    respx.get(
        url__startswith=f"https://{mock_async_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
    ).mock(return_value=httpx.Response(200, json=updated_data))

    work_item = ADOAsyncWorkItem(
        data=copy.deepcopy(mock_async_work_item_data),
        client=mock_async_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    assert work_item["System.State"] == "Active"

    await work_item.refresh()

    assert work_item["System.State"] == "Resolved"


@pytest.mark.asyncio
@respx.mock
async def test_work_item_patch(
    mock_async_work_item_data: dict[str, Any],
    mock_async_client: ADOAsyncClient,
    mock_project_id: str,
) -> None:
    """Test patching a work item field."""
    updated_data = copy.deepcopy(mock_async_work_item_data)
    updated_data["fields"]["System.State"] = "Resolved"

    respx.patch(
        url__startswith=f"https://{mock_async_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
    ).mock(return_value=httpx.Response(200, json=updated_data))

    work_item = ADOAsyncWorkItem(
        data=copy.deepcopy(mock_async_work_item_data),
        client=mock_async_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    assert work_item["System.State"] == "Active"

    await work_item.patch("System.State", "Resolved")

    assert work_item["System.State"] == "Resolved"


@pytest.mark.asyncio
@respx.mock
async def test_work_item_set(
    mock_async_work_item_data: dict[str, Any],
    mock_async_client: ADOAsyncClient,
    mock_project_id: str,
) -> None:
    """Test setting a field using the async set method."""
    updated_data = copy.deepcopy(mock_async_work_item_data)
    updated_data["fields"]["System.Title"] = "New Title"

    respx.patch(
        url__startswith=f"https://{mock_async_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
    ).mock(return_value=httpx.Response(200, json=updated_data))

    work_item = ADOAsyncWorkItem(
        data=copy.deepcopy(mock_async_work_item_data),
        client=mock_async_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    await work_item.set("System.Title", "New Title")

    assert work_item["System.Title"] == "New Title"


@pytest.mark.asyncio
async def test_work_item_repr(
    mock_async_work_item_data: dict[str, Any],
    mock_async_workitems_client: ADOAsyncWorkItemsClient,
) -> None:
    """Test work item string representation."""
    work_item = ADOAsyncWorkItem(
        data=mock_async_work_item_data,
        client=mock_async_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    repr_str = repr(work_item)
    assert "ADOAsyncWorkItem" in repr_str
    assert "12345" in repr_str
    assert "Bug" in repr_str


@pytest.mark.asyncio
async def test_work_item_no_id_patch_raises(
    mock_async_workitems_client: ADOAsyncWorkItemsClient,
) -> None:
    """Test that patching without an ID raises an exception."""
    work_item_data: dict[str, Any] = {"fields": {"System.Title": "Test"}}
    work_item = ADOAsyncWorkItem(
        data=work_item_data,
        client=mock_async_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    with pytest.raises(ADOException):
        await work_item.patch("System.State", "Active")


@pytest.mark.asyncio
async def test_work_item_no_id_refresh_raises(
    mock_async_workitems_client: ADOAsyncWorkItemsClient,
) -> None:
    """Test that refreshing without an ID raises an exception."""
    work_item_data: dict[str, Any] = {"fields": {"System.Title": "Test"}}
    work_item = ADOAsyncWorkItem(
        data=work_item_data,
        client=mock_async_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    with pytest.raises(ADOException):
        await work_item.refresh()
