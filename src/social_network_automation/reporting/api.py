"""Sanitized API evidence for Allure."""

import json
from collections.abc import Mapping
from typing import Any

import httpx

from social_network_automation.reporting.artifacts import attach_text

SENSITIVE_KEYS = frozenset({"password", "token", "authorization", "cookie", "set-cookie"})


def redact(value: Any) -> Any:
    """Recursively redact credentials from report data."""
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if str(key).lower() in SENSITIVE_KEYS else redact(nested)
            for key, nested in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def attach_api_exchange(
    *,
    method: str,
    path: str,
    request_headers: Mapping[str, str],
    request_body: Any,
    response: httpx.Response,
) -> None:
    """Attach one sanitized request/response exchange."""
    try:
        response_body: Any = response.json()
    except ValueError:
        response_body = response.text
    payload = {
        "request": {
            "method": method.upper(),
            "path": path,
            "headers": redact(request_headers),
            "body": redact(request_body),
        },
        "response": {"status": response.status_code, "body": redact(response_body)},
    }
    attach_text(json.dumps(payload, indent=2, default=str), name=f"{method.upper()} {path}")
