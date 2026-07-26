"""Reusable response assertions for tests."""

from collections.abc import Mapping, Sequence
from typing import Any

import httpx

from social_network_automation.api.models import ErrorResponse


def assert_error(response: httpx.Response, status: int, code: str) -> ErrorResponse:
    """Assert and parse a structured backend error."""
    assert response.status_code == status
    error = ErrorResponse.model_validate(response.json())
    assert error.code == code
    return error


def assert_no_password_data(value: Any) -> None:
    """Assert recursively that no password key or bcrypt hash is serialized."""
    if isinstance(value, Mapping):
        for key, nested in value.items():
            assert str(key).lower() != "password"
            assert_no_password_data(nested)
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for nested in value:
            assert_no_password_data(nested)
    elif isinstance(value, str):
        assert not value.startswith(("$2a$", "$2b$", "$2y$"))
