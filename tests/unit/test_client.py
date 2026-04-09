# THIS FILE IS AUTO-GENERATED FROM tests/unit/_async/test_client.py. DO NOT EDIT.

"""Unit tests for the async ADOClient class."""

# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnusedImport=false

import httpx
import respx
from simple_ado import ADOClient
from simple_ado.auth import ADOAuth, ADOTokenAuth


# pylint: disable=line-too-long
def test_client_initialization(mock_tenant: str, mock_auth: ADOAuth) -> None:
    """Test that async client initializes correctly."""
    with ADOClient(tenant=mock_tenant, auth=mock_auth) as client:
        assert client.http_client.tenant == mock_tenant
        assert hasattr(client, "builds")
        assert hasattr(client, "git")
        assert hasattr(client, "pipelines")
        assert hasattr(client, "workitems")


def test_client_has_all_sub_clients(mock_client: ADOClient) -> None:
    """Test that async client has all expected sub-clients."""
    expected_clients = [
        "audit",
        "builds",
        "endpoints",
        "git",
        "governance",
        "graph",
        "identities",
        "pipelines",
        "pools",
        "security",
        "user",
        "wiki",
        "workitems",
    ]

    for client_name in expected_clients:
        assert hasattr(mock_client, client_name), f"Missing {client_name} client"


@respx.mock
def test_verify_access_success(mock_client: ADOClient) -> None:
    """Test verify_access with successful response."""
    respx.get(
        f"https://{mock_client.http_client.tenant}.visualstudio.com/_apis/projects",
    ).mock(return_value=httpx.Response(200, json={"value": [], "count": 0}))

    result = mock_client.verify_access()
    assert result is True


@respx.mock
def test_verify_access_failure(mock_client: ADOClient) -> None:
    """Test verify_access with failed response."""
    respx.get(
        f"https://{mock_client.http_client.tenant}.visualstudio.com/_apis/projects",
    ).mock(return_value=httpx.Response(401))

    result = mock_client.verify_access()
    assert result is False


def test_auth_types() -> None:
    """Test different authentication types."""
    token_auth = ADOTokenAuth("test-token")
    with ADOClient(tenant="test", auth=token_auth) as client:
        assert client.http_client.auth == token_auth


@respx.mock
def test_custom_get(mock_client: ADOClient, mock_project_id: str) -> None:
    """Test custom_get method."""
    base_url = f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/test/endpoint"

    route = respx.get(url__startswith=base_url).mock(
        return_value=httpx.Response(200, json={"data": "test"})
    )

    response = mock_client.custom_get(
        url_fragment="test/endpoint",
        parameters={"api-version": "6.0"},
        project_id=mock_project_id,
    )

    assert response.status_code == 200
    assert route.called
    assert "api-version=6.0" in str(route.calls[0].request.url)


def test_context_manager(mock_tenant: str, mock_auth: ADOAuth) -> None:
    """Test that the async client works as a context manager."""
    with ADOClient(tenant=mock_tenant, auth=mock_auth) as client:
        assert client.http_client.tenant == mock_tenant
