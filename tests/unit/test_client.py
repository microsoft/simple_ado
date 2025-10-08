"""Unit tests for the main ADOClient class."""

import pytest
import responses
from simple_ado import ADOClient
from simple_ado.auth import ADOTokenAuth


def test_client_initialization(mock_tenant, mock_auth):
    """Test that client initializes correctly."""
    client = ADOClient(tenant=mock_tenant, auth=mock_auth)

    assert client.http_client.tenant == mock_tenant
    assert hasattr(client, "builds")
    assert hasattr(client, "git")
    assert hasattr(client, "pipelines")
    assert hasattr(client, "workitems")


def test_client_has_all_sub_clients(mock_client):
    """Test that client has all expected sub-clients."""
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


@responses.activate
def test_verify_access_success(mock_client):
    """Test verify_access with successful response."""
    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/_apis/projects",
        json={"value": [], "count": 0},
        status=200,
    )

    result = mock_client.verify_access()
    assert result is True


@responses.activate
def test_verify_access_failure(mock_client):
    """Test verify_access with failed response."""
    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/_apis/projects",
        status=401,
    )

    result = mock_client.verify_access()
    assert result is False


def test_auth_types():
    """Test different authentication types."""
    # Token auth
    token_auth = ADOTokenAuth("test-token")
    client1 = ADOClient(tenant="test", auth=token_auth)
    assert client1.http_client.auth == token_auth

    # Can add more auth types when needed


@responses.activate
def test_custom_get(mock_client, mock_project_id):
    """Test custom_get method."""
    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/{mock_project_id}/_apis/test/endpoint",
        json={"data": "test"},
        status=200,
    )

    response = mock_client.custom_get(
        url_fragment="test/endpoint", parameters={"api-version": "6.0"}, project_id=mock_project_id
    )

    assert response.status_code == 200
