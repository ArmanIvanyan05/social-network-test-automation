"""UI failure artifact utilities."""

import re
from pathlib import Path
from typing import Protocol, cast

import allure


class _AttachContent(Protocol):
    def __call__(
        self,
        body: bytes | str,
        name: str | None = None,
        attachment_type: object | None = None,
        extension: str | None = None,
    ) -> None:
        """Attach in-memory content."""


class _AttachFile(Protocol):
    def __call__(
        self,
        source: str,
        name: str | None = None,
        attachment_type: object | None = None,
        extension: str | None = None,
    ) -> None:
        """Attach a file from disk."""


_attach_content = cast("_AttachContent", allure.attach)
_attach_file = cast("_AttachFile", allure.attach.file)


def artifact_stem(node_id: str) -> str:
    """Create a filesystem-safe artifact stem from a pytest node ID."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", node_id).strip("_")


def attach_screenshot(screenshot: bytes, *, name: str) -> None:
    """Attach a PNG screenshot to the active Allure test."""
    _attach_content(screenshot, name=name, attachment_type="image/png", extension="png")


def attach_trace(trace_path: Path, *, name: str) -> None:
    """Attach a Playwright trace archive to the active Allure test."""
    _attach_file(
        str(trace_path),
        name=name,
        attachment_type="application/zip",
        extension="zip",
    )


def attach_text(content: str, *, name: str) -> None:
    """Attach sanitized plain text to the active Allure test."""
    _attach_content(content, name=name, attachment_type="text/plain", extension="txt")
