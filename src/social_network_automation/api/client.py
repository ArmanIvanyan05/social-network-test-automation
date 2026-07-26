"""Synchronous HTTP client foundation."""

import logging
from types import TracebackType
from typing import Any, Self

import httpx

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
        json: Any | None = None,
    ) -> httpx.Response:
        """Send a request and return the unmodified response for test assertions."""
        headers = {"Authorization": f"Bearer {token}"} if token else None
        request_options: dict[str, Any] = {}
        if headers is not None:
            request_options["headers"] = headers
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
        response = self._client.request(method, path, **request_options)
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
