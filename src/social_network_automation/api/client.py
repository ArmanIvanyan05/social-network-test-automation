"""Synchronous HTTP client foundation."""

import logging
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Self

import httpx

from social_network_automation.reporting.allure_helpers import allure_step
from social_network_automation.reporting.api import attach_api_exchange

LOGGER = logging.getLogger(__name__)


class ApiClient:
    """Small typed wrapper around a reusable synchronous httpx client."""

    def __init__(self, *, base_url: str, timeout_seconds: float) -> None:
        """Create a client with a shared base URL and request timeout."""
        self._client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(timeout_seconds),
            headers={"Accept": "application/json"},
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        headers: Mapping[str, str] | None = None,
        json: Any | None = None,
    ) -> httpx.Response:
        """Send a request and return the unmodified response for test assertions."""
        request_headers = dict(headers or {})
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        request_options: dict[str, Any] = {}
        if request_headers:
            request_options["headers"] = request_headers
        if json is not None:
            request_options["json"] = json
        LOGGER.info(
            "api_request",
            extra={
                "method": method.upper(),
                "path": path,
                "authenticated": token is not None,
            },
        )
        with allure_step(f"{method.upper()} {path}"):
            response = self._client.request(method, path, **request_options)
        attach_api_exchange(
            method=method,
            path=path,
            request_headers=request_headers,
            request_body=json,
            response=response,
        )
        LOGGER.info(
            "api_response",
            extra={
                "method": method.upper(),
                "path": path,
                "status_code": response.status_code,
            },
        )
        return response

    def get(self, path: str, *, token: str | None = None) -> httpx.Response:
        """Send a GET request."""
        return self.request("GET", path, token=token)

    def close(self) -> None:
        """Close the underlying connection pool."""
        self._client.close()

    def __enter__(self) -> Self:
        """Support explicit context-managed use."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close resources when leaving a context manager."""
        self.close()
