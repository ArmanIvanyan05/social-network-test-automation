"""Typed adapters around Allure's dynamically typed metadata API."""

from typing import Protocol, cast

import allure


class _SetLabel(Protocol):
    def __call__(self, label: str) -> None:
        """Set one Allure label."""


_set_feature = cast("_SetLabel", allure.dynamic.feature)
_set_story = cast("_SetLabel", allure.dynamic.story)


def set_allure_labels(*, feature: str, story: str) -> None:
    """Set typed feature and story labels for the active test."""
    _set_feature(feature)
    _set_story(story)
