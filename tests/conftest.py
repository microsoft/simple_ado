"""Pytest configuration and shared fixtures for simple_ado tests."""

import json
import os
from pathlib import Path
from typing import Any, Callable, cast

import pytest
from pytest import Config
from simple_ado import ADOClient
from simple_ado.auth import ADOTokenAuth


# Test data directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(name="mock_tenant")
def fixture_mock_tenant() -> str:
    """Return a mock tenant name."""
    return "test-tenant"


@pytest.fixture(name="mock_project_id")
def fixture_mock_project_id() -> str:
    """Return a mock project ID."""
    return "test-project-123"


@pytest.fixture(name="mock_repository_id")
def fixture_mock_repository_id() -> str:
    """Return a mock repository ID."""
    return "test-repo-456"


@pytest.fixture(name="mock_feed_id")
def fixture_mock_feed_id() -> str:
    """Return a mock feed ID."""
    return "test-feed-789"


@pytest.fixture(name="mock_auth")
def fixture_mock_auth() -> ADOTokenAuth:
    """Return a mock authentication object."""
    return ADOTokenAuth("mock-token-12345")


@pytest.fixture(name="mock_client")
def fixture_mock_client(mock_tenant: str, mock_auth: ADOTokenAuth) -> ADOClient:
    """Return a mock ADO client."""
    return ADOClient(tenant=mock_tenant, auth=mock_auth)


@pytest.fixture(name="load_fixture")
def fixture_load_fixture() -> Callable[[str], dict[str, Any]]:
    """Load a JSON fixture file."""

    def _load(filename: str) -> dict[str, Any]:
        fixture_path = FIXTURES_DIR / filename
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_path}")
        with open(fixture_path, "r", encoding="utf-8") as f:
            return cast(dict[str, Any], json.load(f))

    return _load


def pytest_configure(config: Config) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require real ADO access)"
    )
    config.addinivalue_line("markers", "destructive: marks tests that modify ADO resources")


def pytest_collection_modifyitems(config: Config, items: list[pytest.Item]) -> None:
    """Automatically skip integration tests unless --integration flag is used."""
    if config.getoption("--integration"):
        # Running with --integration flag, don't skip anything
        return

    skip_integration = pytest.mark.skip(reason="need --integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests that require ADO access",
    )


# Integration test fixtures (only used when --integration is specified)


@pytest.fixture(name="integration_tenant")
def fixture_integration_tenant() -> str:
    """Get tenant from environment for integration tests."""
    tenant = os.getenv("SIMPLE_ADO_TENANT")
    if not tenant:
        raise ValueError("SIMPLE_ADO_TENANT environment variable not set")
    return tenant


@pytest.fixture(name="integration_token")
def fixture_integration_token() -> str:
    """Get token from environment for integration tests."""
    token = os.getenv("SIMPLE_ADO_BASE_TOKEN")
    if not token:
        raise ValueError("SIMPLE_ADO_BASE_TOKEN environment variable not set")
    return token


@pytest.fixture(name="integration_project_id")
def fixture_integration_project_id() -> str:
    """Get project ID from environment for integration tests."""
    project_id = os.getenv("SIMPLE_ADO_PROJECT_ID")
    if not project_id:
        raise ValueError("SIMPLE_ADO_PROJECT_ID environment variable not set")
    return project_id


@pytest.fixture(name="integration_repo_id")
def fixture_integration_repo_id() -> str:
    """Get repository ID from environment for integration tests."""
    repo_id = os.getenv("SIMPLE_ADO_REPO_ID")
    if not repo_id:
        raise ValueError("SIMPLE_ADO_REPO_ID environment variable not set")
    return repo_id


@pytest.fixture(name="integration_client")
def fixture_integration_client(integration_tenant: str, integration_token: str) -> ADOClient:
    """Return a real ADO client for integration tests."""
    auth = ADOTokenAuth(integration_token)
    return ADOClient(tenant=integration_tenant, auth=auth)
