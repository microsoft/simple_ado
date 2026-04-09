# THIS FILE IS AUTO-GENERATED FROM tests/unit/_async/test_builds.py. DO NOT EDIT.

"""Unit tests for the async Builds client."""

# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnusedImport=false

from typing import Any, Callable

import httpx
import respx
from simple_ado import ADOClient
from simple_ado.builds import BuildQueryOrder


# pylint: disable=line-too-long
@respx.mock
def test_get_builds(
    mock_client: ADOClient,
    mock_project_id: str,
    load_fixture: Callable[[str], dict[str, Any]],
) -> None:
    """Test getting builds."""
    builds_data = load_fixture("builds_list.json")
    base_url = f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds/"

    route = respx.get(url__startswith=base_url).mock(
        return_value=httpx.Response(200, json=builds_data)
    )

    builds = []
    for build in mock_client.builds.get_builds(project_id=mock_project_id):
        builds.append(build)

    assert len(builds) == 2
    assert builds[0]["id"] == 12345
    assert builds[0]["status"] == "completed"
    assert route.called
    assert "api-version=" in str(route.calls[0].request.url)


@respx.mock
def test_get_builds_with_definition_filter(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test getting builds filtered by definition."""
    base_url = f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds/"

    route = respx.get(url__startswith=base_url, params__contains={"definitions": "100,101"}).mock(
        return_value=httpx.Response(200, json={"value": []})
    )

    builds = []
    for build in mock_client.builds.get_builds(project_id=mock_project_id, definitions=[100, 101]):
        builds.append(build)

    assert not builds
    assert route.called


@respx.mock
def test_get_builds_with_order(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test getting builds with specific order."""
    base_url = f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds/"

    route = respx.get(
        url__startswith=base_url, params__contains={"queryOrder": "finishTimeDescending"}
    ).mock(return_value=httpx.Response(200, json={"value": []}))

    builds = []
    for build in mock_client.builds.get_builds(
        project_id=mock_project_id, order=BuildQueryOrder.FINISH_TIME_DESCENDING
    ):
        builds.append(build)

    assert not builds
    assert route.called


@respx.mock
def test_build_info(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test getting build info."""
    build_id = 12345
    base_url = f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds/{build_id}"
    build_data: dict[str, Any] = {
        "id": build_id,
        "buildNumber": "20231001.1",
        "status": "completed",
        "result": "succeeded",
    }

    route = respx.get(url__startswith=base_url).mock(
        return_value=httpx.Response(200, json=build_data)
    )

    result = mock_client.builds.build_info(project_id=mock_project_id, build_id=build_id)

    assert result["id"] == build_id
    assert result["result"] == "succeeded"
    assert route.called
    request_url = str(route.calls[0].request.url)
    assert f"/builds/{build_id}" in request_url
    assert "api-version=" in request_url


@respx.mock
def test_queue_build(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test queueing a new build."""
    definition_id = 100
    source_branch = "refs/heads/main"
    variables = {"myVar": "myValue"}

    queued_build: dict[str, Any] = {"id": 99999, "buildNumber": "queued", "status": "notStarted"}
    base_url = f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds"

    route = respx.post(url__startswith=base_url).mock(
        return_value=httpx.Response(200, json=queued_build)
    )

    result = mock_client.builds.queue_build(
        project_id=mock_project_id,
        definition_id=definition_id,
        source_branch=source_branch,
        variables=variables,
    )

    assert result["id"] == 99999
    assert result["status"] == "notStarted"
    assert route.called
    assert "api-version=" in str(route.calls[0].request.url)


@respx.mock
def test_list_artifacts(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test listing build artifacts."""
    build_id = 12345
    artifacts_data: dict[str, Any] = {
        "value": [
            {"id": 1, "name": "drop", "resource": {"type": "Container"}},
            {"id": 2, "name": "logs", "resource": {"type": "Container"}},
        ]
    }

    respx.get(
        url__startswith=f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds/{build_id}/artifacts",
    ).mock(return_value=httpx.Response(200, json=artifacts_data))

    result = mock_client.builds.list_artifacts(project_id=mock_project_id, build_id=build_id)

    assert len(result) == 2
    assert result[0]["name"] == "drop"


@respx.mock
def test_get_definitions(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test getting build definitions."""
    definitions_data: dict[str, Any] = {
        "value": [{"id": 100, "name": "CI Pipeline"}, {"id": 101, "name": "Release Pipeline"}]
    }

    respx.get(
        url__startswith=f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/definitions",
    ).mock(return_value=httpx.Response(200, json=definitions_data))

    result = mock_client.builds.get_definitions(project_id=mock_project_id)

    assert len(result) == 2
    assert result[0]["name"] == "CI Pipeline"


@respx.mock
def test_get_definition(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test getting a specific build definition."""
    definition_id = 100
    definition_data: dict[str, Any] = {
        "id": definition_id,
        "name": "CI Pipeline",
        "type": "build",
        "quality": "definition",
    }

    respx.get(
        url__startswith=f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/definitions/{definition_id}",
    ).mock(return_value=httpx.Response(200, json=definition_data))

    result = mock_client.builds.get_definition(
        project_id=mock_project_id, definition_id=definition_id
    )

    assert result["id"] == definition_id
    assert result["name"] == "CI Pipeline"


@respx.mock
def test_delete_definition(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test deleting a build definition."""
    definition_id = 100

    route = respx.delete(
        url__startswith=f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/definitions/{definition_id}",
    ).mock(return_value=httpx.Response(204))

    # Should not raise any exception
    mock_client.builds.delete_definition(project_id=mock_project_id, definition_id=definition_id)

    assert route.called
