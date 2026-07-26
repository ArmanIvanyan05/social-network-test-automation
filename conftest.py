"""Project-wide pytest configuration and fixture registration."""

from collections.abc import Generator

import pytest

from social_network_automation.fixtures.state import UI_TEST_FAILED
from social_network_automation.reporting import configure_logging

pytest_plugins = ["social_network_automation.fixtures.core"]


def pytest_configure() -> None:
    """Configure structured logging before test execution."""
    configure_logging()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """Record call-phase UI failures for fixture teardown diagnostics."""
    report = yield
    if report.when == "call":
        item.stash[UI_TEST_FAILED] = report.failed
    return report
