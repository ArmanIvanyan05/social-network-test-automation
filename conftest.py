"""Project-wide pytest configuration and fixture registration."""

from collections.abc import Generator

import pytest

from social_network_automation.fixtures.state import UI_TEST_FAILED
from social_network_automation.reporting import configure_logging
from social_network_automation.reporting.allure_helpers import set_allure_metadata

pytest_plugins = ["social_network_automation.fixtures.core"]


def pytest_configure() -> None:
    """Configure structured logging before test execution."""
    configure_logging()


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Add consistent human-readable Allure metadata."""
    path = item.path.as_posix()
    story = item.path.stem.removeprefix("test_").replace("_", " ").title()
    if "/tests/api/" in path:
        feature = "REST API"
    elif "/tests/ui/" in path:
        feature = "Browser UI"
    elif "/tests/e2e/" in path:
        feature = "Hybrid E2E"
    else:
        feature = "Environment"
    title = item.name.removeprefix("test_").replace("_", " ").capitalize()
    set_allure_metadata(feature=feature, story=story, title=title)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """Record call-phase UI failures for fixture teardown diagnostics."""
    report = yield
    if report.when == "call":
        item.stash[UI_TEST_FAILED] = report.failed
    return report
