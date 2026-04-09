"""Unit tests for ADOAsyncWorkItem.get_field (auto-refresh)."""

import copy
import logging
from typing import Any

import httpx
import pytest
import respx
from simple_ado._async import ADOAsyncClient
from simple_ado._async.work_item import ADOAsyncWorkItem


@pytest.fixture(name="async_work_item_data")
def fixture_async_work_item_data() -> dict[str, Any]:
    """Return mock work item data."""
    return {
        "id": 12345,
        "rev": 1,
        "fields": {
            "System.Title": "Test Work Item",
            "System.State": "Active",
            "System.WorkItemType": "Bug",
        },
        "url": "https://test.visualstudio.com/_apis/wit/workitems/12345",
    }


@pytest.mark.asyncio
@respx.mock
async def test_get_field_existing_field(
    async_work_item_data: dict[str, Any], mock_async_client: ADOAsyncClient, mock_project_id: str
) -> None:
    """get_field should return field value without refresh when field exists."""
    work_item = ADOAsyncWorkItem(
        data=copy.deepcopy(async_work_item_data),
        client=mock_async_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    result = await work_item.get_field("System.Title")
    assert result == "Test Work Item"


@pytest.mark.asyncio
@respx.mock
async def test_get_field_missing_triggers_refresh(
    async_work_item_data: dict[str, Any], mock_async_client: ADOAsyncClient, mock_project_id: str
) -> None:
    """get_field should refresh from server when field is missing."""
    refreshed_data = copy.deepcopy(async_work_item_data)
    refreshed_data["fields"]["Custom.Field"] = "found after refresh"

    respx.get(
        url__startswith=f"https://{mock_async_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
    ).mock(return_value=httpx.Response(200, json=refreshed_data))

    work_item = ADOAsyncWorkItem(
        data=copy.deepcopy(async_work_item_data),
        client=mock_async_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    result = await work_item.get_field("Custom.Field")
    assert result == "found after refresh"


@pytest.mark.asyncio
@respx.mock
async def test_get_field_missing_still_raises_after_refresh(
    async_work_item_data: dict[str, Any], mock_async_client: ADOAsyncClient, mock_project_id: str
) -> None:
    """get_field should raise KeyError if field is still missing after refresh."""
    respx.get(
        url__startswith=f"https://{mock_async_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
    ).mock(return_value=httpx.Response(200, json=async_work_item_data))

    work_item = ADOAsyncWorkItem(
        data=copy.deepcopy(async_work_item_data),
        client=mock_async_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    with pytest.raises(KeyError):
        await work_item.get_field("NonExistent.Field")


@pytest.mark.asyncio
async def test_get_field_no_auto_refresh(
    async_work_item_data: dict[str, Any], mock_async_client: ADOAsyncClient, mock_project_id: str
) -> None:
    """get_field with auto_refresh=False should raise immediately."""
    work_item = ADOAsyncWorkItem(
        data=copy.deepcopy(async_work_item_data),
        client=mock_async_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    with pytest.raises(KeyError):
        await work_item.get_field("NonExistent.Field", auto_refresh=False)
