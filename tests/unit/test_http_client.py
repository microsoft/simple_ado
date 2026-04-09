# THIS FILE IS AUTO-GENERATED FROM tests/unit/_async/test_http_client.py. DO NOT EDIT.

"""Unit tests for the async HTTP client error paths and rate limiting."""

# pylint: disable=protected-access
# pyright: reportPrivateUsage=false

import datetime
import logging
from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import httpx
import pytest
import respx
from simple_ado.auth import ADOTokenAuth
from simple_ado.http_client import ADOHTTPClient, _is_retryable_get_failure
from simple_ado.exceptions import ADOException, ADOHTTPException


@pytest.fixture(name="http_client")
def fixture_http_client() -> Generator[ADOHTTPClient]:
    """Return a mock async HTTP client."""
    auth = ADOTokenAuth("mock-token")
    client = ADOHTTPClient(
        tenant="test-tenant",
        auth=auth,
        user_agent="test",
        log=logging.getLogger("test"),
    )
    yield client
    client.close()


class TestValidateResponse:
    """Tests for validate_response."""

    def test_success(self, http_client: ADOHTTPClient) -> None:
        """200 response should not raise."""
        response = httpx.Response(200, json={"ok": True})
        http_client.validate_response(response)

    def test_non_200_raises(self, http_client: ADOHTTPClient) -> None:
        """Non-200 response should raise ADOHTTPException."""
        response = httpx.Response(404, json={"error": "not found"})
        with pytest.raises(ADOHTTPException) as exc_info:
            http_client.validate_response(response)
        assert exc_info.value.response.status_code == 404

    def test_server_error_raises(self, http_client: ADOHTTPClient) -> None:
        """500 response should raise ADOHTTPException."""
        response = httpx.Response(500, text="Internal Server Error")
        with pytest.raises(ADOHTTPException):
            http_client.validate_response(response)


class TestDecodeResponse:
    """Tests for decode_response."""

    def test_valid_json(self, http_client: ADOHTTPClient) -> None:
        """Valid JSON response should be decoded."""
        data = {"id": 1, "name": "test"}
        response = httpx.Response(200, json=data)
        result = http_client.decode_response(response)
        assert result == data

    def test_non_200_raises_before_decode(self, http_client: ADOHTTPClient) -> None:
        """Non-200 response should raise before attempting decode."""
        response = httpx.Response(401, json={"error": "unauthorized"})
        with pytest.raises(ADOHTTPException):
            http_client.decode_response(response)

    def test_invalid_json_raises(self, http_client: ADOHTTPClient) -> None:
        """Non-JSON response should raise ADOException."""
        response = httpx.Response(200, text="not json")
        with pytest.raises(ADOException, match="did not contain JSON"):
            http_client.decode_response(response)


class TestExtractValue:
    """Tests for extract_value."""

    def test_valid_value(self, http_client: ADOHTTPClient) -> None:
        """Response with 'value' key should extract it."""
        data: dict[str, Any] = {"value": [{"id": 1}], "count": 1}
        result = http_client.extract_value(data)
        assert result == [{"id": 1}]

    def test_missing_value_raises(self, http_client: ADOHTTPClient) -> None:
        """Response without 'value' key should raise ADOException."""
        with pytest.raises(ADOException, match="did not contain a value"):
            http_client.extract_value({"count": 0})


class TestRateLimiting:
    """Tests for rate limiting logic."""

    def test_track_retry_after(self, http_client: ADOHTTPClient) -> None:
        """Retry-After header should set _not_before."""
        response = httpx.Response(200, headers={"Retry-After": "5"})
        http_client._track_rate_limit(response)
        assert http_client._not_before is not None
        delta = http_client._not_before - datetime.datetime.now()
        assert 3 < delta.total_seconds() <= 5

    def test_track_retry_after_capped(self, http_client: ADOHTTPClient) -> None:
        """Retry-After > 15 should be capped at 15."""
        response = httpx.Response(200, headers={"Retry-After": "120"})
        http_client._track_rate_limit(response)
        assert http_client._not_before is not None
        delta = http_client._not_before - datetime.datetime.now()
        assert delta.total_seconds() <= 16

    def test_track_low_remaining(self, http_client: ADOHTTPClient) -> None:
        """Low X-RateLimit-Remaining should set a 1-second delay."""
        response = httpx.Response(200, headers={"X-RateLimit-Remaining": "5"})
        http_client._track_rate_limit(response)
        assert http_client._not_before is not None

    def test_track_high_remaining_clears(self, http_client: ADOHTTPClient) -> None:
        """High X-RateLimit-Remaining should clear the delay."""
        http_client._not_before = datetime.datetime.now() + datetime.timedelta(seconds=10)
        response = httpx.Response(200, headers={"X-RateLimit-Remaining": "100"})
        http_client._track_rate_limit(response)
        assert http_client._not_before is None

    def test_wait_skips_when_no_limit(self, http_client: ADOHTTPClient) -> None:
        """_wait should return immediately when _not_before is None."""
        http_client._not_before = None
        http_client._wait()

    def test_wait_clears_expired(self, http_client: ADOHTTPClient) -> None:
        """_wait should clear _not_before when it's in the past."""
        http_client._not_before = datetime.datetime.now() - datetime.timedelta(seconds=1)
        http_client._wait()
        assert http_client._not_before is None


class TestHTTPMethods:
    """Tests for HTTP methods honoring rate limiting."""

    @respx.mock
    def test_get_non_200_raises(self, http_client: ADOHTTPClient) -> None:
        """GET returning non-200 should raise on validate_response."""
        respx.get("https://example.com/api").mock(
            return_value=httpx.Response(403, json={"error": "forbidden"})
        )
        response = http_client.get("https://example.com/api")
        with pytest.raises(ADOHTTPException):
            http_client.validate_response(response)

    @respx.mock
    def test_post_calls_wait_and_track(self, http_client: ADOHTTPClient) -> None:
        """POST should call _wait and _track_rate_limit."""
        respx.post("https://example.com/api").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        with patch.object(http_client, "_wait") as mock_wait, patch.object(
            http_client, "_track_rate_limit"
        ) as mock_track:
            http_client.post("https://example.com/api", json_data={"key": "value"})
            mock_wait.assert_called_once()
            mock_track.assert_called_once()

    @respx.mock
    def test_patch_calls_wait_and_track(self, http_client: ADOHTTPClient) -> None:
        """PATCH should call _wait and _track_rate_limit."""
        respx.patch("https://example.com/api").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        with patch.object(http_client, "_wait") as mock_wait, patch.object(
            http_client, "_track_rate_limit"
        ) as mock_track:
            http_client.patch("https://example.com/api", json_data={"key": "value"})
            mock_wait.assert_called_once()
            mock_track.assert_called_once()

    @respx.mock
    def test_put_calls_wait_and_track(self, http_client: ADOHTTPClient) -> None:
        """PUT should call _wait and _track_rate_limit."""
        respx.put("https://example.com/api").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        with patch.object(http_client, "_wait") as mock_wait, patch.object(
            http_client, "_track_rate_limit"
        ) as mock_track:
            http_client.put("https://example.com/api", json_data={"key": "value"})
            mock_wait.assert_called_once()
            mock_track.assert_called_once()

    @respx.mock
    def test_delete_calls_wait_and_track(self, http_client: ADOHTTPClient) -> None:
        """DELETE should call _wait and _track_rate_limit."""
        respx.delete("https://example.com/api").mock(return_value=httpx.Response(204))
        with patch.object(http_client, "_wait") as mock_wait, patch.object(
            http_client, "_track_rate_limit"
        ) as mock_track:
            http_client.delete("https://example.com/api")
            mock_wait.assert_called_once()
            mock_track.assert_called_once()


class TestRetryableStatusCodes:
    """Tests for retryable status code classification."""

    def test_408_is_retryable(self) -> None:
        """408 Request Timeout should be retryable."""
        response = httpx.Response(408)
        exc = ADOHTTPException("timeout", response)
        assert _is_retryable_get_failure(exc) is True

    def test_429_is_retryable(self) -> None:
        """429 Too Many Requests should be retryable."""
        response = httpx.Response(429)
        exc = ADOHTTPException("rate limited", response)
        assert _is_retryable_get_failure(exc) is True

    def test_400_is_retryable(self) -> None:
        """400 Bad Request should be retryable (transient ADO errors)."""
        response = httpx.Response(400)
        exc = ADOHTTPException("bad request", response)
        assert _is_retryable_get_failure(exc) is True

    def test_500_is_retryable(self) -> None:
        """500 Internal Server Error should be retryable."""
        response = httpx.Response(500)
        exc = ADOHTTPException("server error", response)
        assert _is_retryable_get_failure(exc) is True

    def test_401_not_retryable(self) -> None:
        """401 Unauthorized should not be retryable."""
        response = httpx.Response(401)
        exc = ADOHTTPException("unauthorized", response)
        assert _is_retryable_get_failure(exc) is False

    def test_403_not_retryable(self) -> None:
        """403 Forbidden should not be retryable."""
        response = httpx.Response(403)
        exc = ADOHTTPException("forbidden", response)
        assert _is_retryable_get_failure(exc) is False

    def test_404_not_retryable(self) -> None:
        """404 Not Found should not be retryable."""
        response = httpx.Response(404)
        exc = ADOHTTPException("not found", response)
        assert _is_retryable_get_failure(exc) is False

    def test_non_http_exception_not_retryable(self) -> None:
        """Non-ADOHTTPException should not be retryable."""
        assert _is_retryable_get_failure(ValueError("boom")) is False
