# Testing Guide for simple_ado

## Overview

This project uses **pure pytest** with a two-tier testing strategy:

1. **Unit Tests** (in `tests/unit/`) - Fast, isolated tests that mock HTTP requests
2. **Integration Tests** (in `tests/integration/`) - Tests against real Azure DevOps (optional)

All tests are written in pytest style (no unittest classes).

## Running Tests

### Run All Unit Tests (Default)

```bash
pytest
```

or

```bash
python -m pytest
```

### Run Only Unit Tests (Explicit)

```bash
pytest tests/unit/
```

### Run Integration Tests

Integration tests require Azure DevOps credentials and are skipped by default.

```bash
# Set environment variables first
export SIMPLE_ADO_BASE_TOKEN="your-ado-token"
export SIMPLE_ADO_TENANT="your-tenant"
export SIMPLE_ADO_PROJECT_ID="your-project-id"
export SIMPLE_ADO_REPO_ID="your-repo-id"

# Run with integration flag
pytest --integration
```

### Run Specific Tests

```bash
# Run a specific test file
pytest tests/unit/test_artifacts.py

# Run a specific test class
pytest tests/unit/test_artifacts.py::TestArtifactsClient

# Run a specific test method
pytest tests/unit/test_artifacts.py::TestArtifactsClient::test_list_packages
```

### Run with Coverage

```bash
pytest --cov=simple_ado --cov-report=html
```

Then open `htmlcov/index.html` to view the coverage report.

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (always run)
│   ├── test_client.py
│   ├── test_artifacts.py
│   ├── test_builds.py
│   └── ...
├── integration/             # Integration tests (optional)
│   ├── test_integration_legacy.py
│   └── ...
└── fixtures/                # Mock response data
    ├── builds_list.json
    ├── packages_list.json
    └── ...
```

## Writing Tests

### Unit Tests

Unit tests mock HTTP responses using the `responses` library. All tests are written in **pure pytest style**:

```python
import responses
from simple_ado import ADOClient

@responses.activate
def test_something(mock_client, mock_project_id) -> None:
    # Mock the HTTP response
    responses.add(
        responses.GET,
        f"https://{mock_client.http_client.tenant}.visualstudio.com/...",
        json={"data": "value"},
        status=200
    )
    
    # Call the method
    result = mock_client.some_method(project_id=mock_project_id)
    
    # Assert the result
    assert result["data"] == "value"
```

### Integration Tests

Integration tests are pure pytest functions marked with `@pytest.mark.integration`:

```python
import pytest

@pytest.mark.integration
def test_real_api(integration_client, integration_project_id):
    # This only runs with --integration flag
    result = integration_client.some_method(project_id=integration_project_id)
    assert result is not None
```

## Fixtures

Common fixtures are defined in `conftest.py`:

- `mock_client` - A mock ADO client
- `mock_tenant` - Mock tenant name
- `mock_project_id` - Mock project ID
- `mock_repository_id` - Mock repository ID
- `mock_feed_id` - Mock feed ID
- `load_fixture` - Load JSON fixture files
- `integration_client` - Real ADO client (integration tests only)
- `integration_project_id` - Real project ID (integration tests only)

## Best Practices

1. **Write unit tests first** - They're fast and don't require credentials
2. **Use pure pytest style** - No unittest.TestCase classes
3. **Mock external dependencies** - Use `responses` to mock HTTP calls
4. **Use fixtures** - Reuse common test data via pytest fixtures
5. **Test edge cases** - Include tests for error conditions
6. **Keep tests isolated** - Each test should be independent
7. **Mark destructive tests** - Use `@pytest.mark.destructive` for tests that modify data
8. **Document complex tests** - Add docstrings explaining what's being tested

## Continuous Integration

The CI pipeline runs:

- Unit tests on every commit/PR
- Code coverage reporting
- Integration tests on nightly builds (with credentials)

## Troubleshooting

### Tests fail with "need --integration option to run"

This is expected. Integration tests are skipped by default. Use `--integration` flag to run them.

### Mock responses not matching

Check that the URL in `responses.add()` matches exactly what the client code generates.

### Fixtures not found

Make sure `conftest.py` is in the `tests/` directory and fixtures are properly defined.

### Import errors

Ensure the package is installed in development mode:
```bash
pip install -e .
```

## Adding New Tests

1. Create a new test file in `tests/unit/` (e.g., `test_newfeature.py`)
2. Import necessary modules and fixtures
3. Write test cases using `@responses.activate` for mocking
4. Add fixture data to `tests/fixtures/` if needed
5. Run tests with `pytest tests/unit/test_newfeature.py`
