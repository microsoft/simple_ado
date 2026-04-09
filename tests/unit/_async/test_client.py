"""Unit tests for the async ADOAsyncClient class."""

# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnusedImport=false

import httpx
import pytest
import respx
from simple_ado._async import ADOAsyncClient
from simple_ado._async.auth import ADOAsyncAuth, ADOAsyncTokenAuth

# pylint: disable=line-too-long


@pytest.mark.asyncio
async def test_client_initialization(mock_tenant: str, mock_async_auth: ADOAsyncAuth) -> None:
    """Test that async client initializes correctly."""
    async with ADOAsyncClient(tenant=mock_tenant, auth=mock_async_auth) as client:
        assert client.http_client.tenant == mock_tenant
        assert hasattr(client, "builds")
        assert hasattr(client, "git")
        assert hasattr(client, "pipelines")
        assert hasattr(client, "workitems")


@pytest.mark.asyncio
async def test_client_has_all_sub_clients(mock_async_client: ADOAsyncClient) -> None:
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
        assert hasattr(mock_async_client, client_name), f"Missing {client_name} client"


@pytest.mark.asyncio
@respx.mock
async def test_verify_access_success(mock_async_client: ADOAsyncClient) -> None:
    """Test verify_access with successful response."""
    respx.get(
        f"https://{mock_async_client.http_client.tenant}.visualstudio.com/_apis/projects",
    ).mock(return_value=httpx.Response(200, json={"value": [], "count": 0}))

    result = await mock_async_client.verify_access()
    assert result is True


@pytest.mark.asyncio
@respx.mock
async def test_verify_access_failure(mock_async_client: ADOAsyncClient) -> None:
    """Test verify_access with failed response."""
    respx.get(
        f"https://{mock_async_client.http_client.tenant}.visualstudio.com/_apis/projects",
    ).mock(return_value=httpx.Response(401))

    result = await mock_async_client.verify_access()
    assert result is False


@pytest.mark.asyncio
async def test_auth_types() -> None:
    """Test different authentication types."""
    token_auth = ADOAsyncTokenAuth("test-token")
    async with ADOAsyncClient(tenant="test", auth=token_auth) as client:
        assert client.http_client.auth == token_auth


@pytest.mark.asyncio
@respx.mock
async def test_custom_get(mock_async_client: ADOAsyncClient, mock_project_id: str) -> None:
    """Test custom_get method."""
    base_url = f"https://{mock_async_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/test/endpoint"

    route = respx.get(url__startswith=base_url).mock(
        return_value=httpx.Response(200, json={"data": "test"})
    )

    response = await mock_async_client.custom_get(
        url_fragment="test/endpoint",
        parameters={"api-version": "6.0"},
        project_id=mock_project_id,
    )

    assert response.status_code == 200
    assert route.called
    assert "api-version=6.0" in str(route.calls[0].request.url)


@pytest.mark.asyncio
async def test_context_manager(mock_tenant: str, mock_async_auth: ADOAsyncAuth) -> None:
    """Test that the async client works as a context manager."""
    async with ADOAsyncClient(tenant=mock_tenant, auth=mock_async_auth) as client:
        assert client.http_client.tenant == mock_tenant
