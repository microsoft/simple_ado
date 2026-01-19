"""Unit tests for the Builds client."""

from typing import Any, Callable

import responses
from simple_ado import ADOClient
from simple_ado.builds import BuildQueryOrder

# pylint: disable=line-too-long


@responses.activate  # pyright: ignore[reportUnknownArgumentType]
def test_get_builds(
    mock_client: ADOClient, mock_project_id: str, load_fixture: Callable[[str], dict[str, Any]]
) -> None:
    """Test getting builds."""
    builds_data = load_fixture("builds_list.json")

    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds/",
        json=builds_data,
        status=200,
    )

    builds = list(mock_client.builds.get_builds(project_id=mock_project_id))

    assert len(builds) == 2
    assert builds[0]["id"] == 12345
    assert builds[0]["status"] == "completed"


@responses.activate
def test_get_builds_with_definition_filter(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test getting builds filtered by definition."""
    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds/",
        json={"value": []},
        status=200,
        match=[
            responses.matchers.query_param_matcher({"api-version": "4.1", "definitions": "100,101"})
        ],
    )

    builds = list(mock_client.builds.get_builds(project_id=mock_project_id, definitions=[100, 101]))

    assert not builds


@responses.activate
def test_get_builds_with_order(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test getting builds with specific order."""
    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds/",
        json={"value": []},
        status=200,
        match=[
            responses.matchers.query_param_matcher(
                {"api-version": "4.1", "queryOrder": "finishTimeDescending"}
            )
        ],
    )

    builds = list(
        mock_client.builds.get_builds(
            project_id=mock_project_id, order=BuildQueryOrder.FINISH_TIME_DESCENDING
        )
    )

    assert not builds


@responses.activate
def test_build_info(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test getting build info."""
    build_id = 12345
    build_data: dict[str, Any] = {
        "id": build_id,
        "buildNumber": "20231001.1",
        "status": "completed",
        "result": "succeeded",
    }

    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds/{build_id}",
        json=build_data,
        status=200,
    )

    result = mock_client.builds.build_info(project_id=mock_project_id, build_id=build_id)

    assert result["id"] == build_id
    assert result["result"] == "succeeded"


@responses.activate
def test_queue_build(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test queueing a new build."""
    definition_id = 100
    source_branch = "refs/heads/main"
    variables = {"myVar": "myValue"}

    queued_build: dict[str, Any] = {"id": 99999, "buildNumber": "queued", "status": "notStarted"}

    responses.add(
        responses.POST,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds",
        json=queued_build,
        status=200,
    )

    result = mock_client.builds.queue_build(
        project_id=mock_project_id,
        definition_id=definition_id,
        source_branch=source_branch,
        variables=variables,
    )

    assert result["id"] == 99999
    assert result["status"] == "notStarted"


@responses.activate
def test_list_artifacts(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test listing build artifacts."""
    build_id = 12345
    artifacts_data: dict[str, Any] = {
        "value": [
            {"id": 1, "name": "drop", "resource": {"type": "Container"}},
            {"id": 2, "name": "logs", "resource": {"type": "Container"}},
        ]
    }

    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/builds/{build_id}/artifacts",
        json=artifacts_data,
        status=200,
    )

    result = mock_client.builds.list_artifacts(project_id=mock_project_id, build_id=build_id)

    assert len(result) == 2
    assert result[0]["name"] == "drop"


@responses.activate
def test_get_definitions(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test getting build definitions."""
    definitions_data: dict[str, Any] = {
        "value": [{"id": 100, "name": "CI Pipeline"}, {"id": 101, "name": "Release Pipeline"}]
    }

    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/definitions",
        json=definitions_data,
        status=200,
    )

    result = mock_client.builds.get_definitions(project_id=mock_project_id)

    assert len(result) == 2
    assert result[0]["name"] == "CI Pipeline"


@responses.activate
def test_get_definition(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test getting a specific build definition."""
    definition_id = 100
    definition_data: dict[str, Any] = {
        "id": definition_id,
        "name": "CI Pipeline",
        "type": "build",
        "quality": "definition",
    }

    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/definitions/{definition_id}",
        json=definition_data,
        status=200,
    )

    result = mock_client.builds.get_definition(
        project_id=mock_project_id, definition_id=definition_id
    )

    assert result["id"] == definition_id
    assert result["name"] == "CI Pipeline"


@responses.activate
def test_delete_definition(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test deleting a build definition."""
    definition_id = 100

    responses.add(
        responses.DELETE,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/build/definitions/{definition_id}",
        status=204,
    )

    # Should not raise any exception
    mock_client.builds.delete_definition(project_id=mock_project_id, definition_id=definition_id)

    assert len(responses.calls) == 1
    assert responses.calls[0].request.method == "DELETE"  # pyright: ignore[reportUnknownMemberType]
