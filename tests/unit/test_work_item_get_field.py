# THIS FILE IS AUTO-GENERATED FROM tests/unit/_async/test_work_item_get_field.py. DO NOT EDIT.

"""Unit tests for ADOWorkItem.get_field (auto-refresh)."""

import copy
import logging
from typing import Any

import httpx
import pytest
import respx
from simple_ado import ADOClient
from simple_ado.work_item import ADOWorkItem


@pytest.fixture(name="work_item_data")
def fixture_work_item_data() -> dict[str, Any]:
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


@respx.mock
def test_get_field_existing_field(
    work_item_data: dict[str, Any], mock_client: ADOClient, mock_project_id: str
) -> None:
    """get_field should return field value without refresh when field exists."""
    work_item = ADOWorkItem(
        data=copy.deepcopy(work_item_data),
        client=mock_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    result = work_item.get_field("System.Title")
    assert result == "Test Work Item"


@respx.mock
def test_get_field_missing_triggers_refresh(
    work_item_data: dict[str, Any], mock_client: ADOClient, mock_project_id: str
) -> None:
    """get_field should refresh from server when field is missing."""
    refreshed_data = copy.deepcopy(work_item_data)
    refreshed_data["fields"]["Custom.Field"] = "found after refresh"

    respx.get(
        url__startswith=f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
    ).mock(return_value=httpx.Response(200, json=refreshed_data))

    work_item = ADOWorkItem(
        data=copy.deepcopy(work_item_data),
        client=mock_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    result = work_item.get_field("Custom.Field")
    assert result == "found after refresh"


@respx.mock
def test_get_field_missing_still_raises_after_refresh(
    work_item_data: dict[str, Any], mock_client: ADOClient, mock_project_id: str
) -> None:
    """get_field should raise KeyError if field is still missing after refresh."""
    respx.get(
        url__startswith=f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
    ).mock(return_value=httpx.Response(200, json=work_item_data))

    work_item = ADOWorkItem(
        data=copy.deepcopy(work_item_data),
        client=mock_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    with pytest.raises(KeyError):
        work_item.get_field("NonExistent.Field")


def test_get_field_no_auto_refresh(
    work_item_data: dict[str, Any], mock_client: ADOClient, mock_project_id: str
) -> None:
    """get_field with auto_refresh=False should raise immediately."""
    work_item = ADOWorkItem(
        data=copy.deepcopy(work_item_data),
        client=mock_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    with pytest.raises(KeyError):
        work_item.get_field("NonExistent.Field", auto_refresh=False)
