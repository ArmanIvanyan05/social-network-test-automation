"""Typed adapters around Allure's dynamically typed public API."""

from contextlib import AbstractContextManager
from typing import Any, Protocol, cast

import allure


class _SetLabel(Protocol):
    def __call__(self, label: str) -> None:
        """Set one Allure label."""


class _SetParameter(Protocol):
    def __call__(self, name: str, value: Any) -> None:
        """Set one Allure parameter."""


class _Step(Protocol):
    def __call__(self, title: str) -> AbstractContextManager[None]:
        """Create an Allure step context."""


_set_feature = cast("_SetLabel", allure.dynamic.feature)
_set_story = cast("_SetLabel", allure.dynamic.story)
_set_title = cast("_SetLabel", allure.dynamic.title)
_set_parameter = cast("_SetParameter", allure.dynamic.parameter)
_step = cast("_Step", allure.step)


def set_allure_metadata(*, feature: str, story: str, title: str | None = None) -> None:
    """Set typed feature, story, and optional title metadata."""
    _set_feature(feature)
    _set_story(story)
    if title is not None:
        _set_title(title)


def set_allure_labels(*, feature: str, story: str) -> None:
    """Set typed feature and story labels for compatibility."""
    set_allure_metadata(feature=feature, story=story)


def set_allure_parameter(name: str, value: Any) -> None:
    """Add a typed runtime parameter."""
    _set_parameter(name, value)


def allure_step(title: str) -> AbstractContextManager[None]:
    """Create a typed report step."""
    return _step(title)
