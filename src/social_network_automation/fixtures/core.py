"""Configuration, API, data, and Playwright fixtures."""

import logging
from collections.abc import Generator

import pytest
from faker import Faker
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)
from playwright.sync_api import Error as PlaywrightError

from social_network_automation.api import ApiClient
from social_network_automation.config import BrowserName, Settings, get_settings
from social_network_automation.data import UserDataFactory
from social_network_automation.fixtures.state import UI_TEST_FAILED
from social_network_automation.reporting.artifacts import (
    artifact_stem,
    attach_screenshot,
    attach_trace,
)

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Provide validated framework configuration."""
    return get_settings()


@pytest.fixture
def api_client(settings: Settings) -> Generator[ApiClient]:
    """Provide an isolated synchronous API client."""
    with ApiClient(
        base_url=settings.api_base_url,
        timeout_seconds=settings.api_timeout_seconds,
    ) as client:
        yield client


@pytest.fixture
def user_data_factory() -> UserDataFactory:
    """Provide unique Faker-backed user test data."""
    return UserDataFactory(Faker())


@pytest.fixture(scope="session")
def playwright_runtime() -> Generator[Playwright]:
    """Start and stop the synchronous Playwright runtime."""
    with sync_playwright() as runtime:
        yield runtime


@pytest.fixture(scope="session")
def browser(
    playwright_runtime: Playwright,
    settings: Settings,
) -> Generator[Browser]:
    """Launch the configured Chromium, Firefox, or WebKit browser."""
    browser_type = {
        BrowserName.CHROMIUM: playwright_runtime.chromium,
        BrowserName.FIREFOX: playwright_runtime.firefox,
        BrowserName.WEBKIT: playwright_runtime.webkit,
    }[settings.browser]
    launched_browser = browser_type.launch(
        headless=settings.headless,
        slow_mo=settings.slow_mo_ms,
    )
    yield launched_browser
    launched_browser.close()


@pytest.fixture
def browser_context(
    browser: Browser,
    settings: Settings,
    request: pytest.FixtureRequest,
) -> Generator[BrowserContext]:
    """Create an isolated context and retain its trace only on failure."""
    context = browser.new_context(ignore_https_errors=settings.ignore_https_errors)
    context.set_default_timeout(settings.ui_timeout_ms)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context

    failed = request.node.stash.get(UI_TEST_FAILED, False)
    try:
        if failed:
            settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
            trace_path = settings.artifacts_dir / f"{artifact_stem(request.node.nodeid)}-trace.zip"
            context.tracing.stop(path=trace_path)
            attach_trace(trace_path, name="Playwright trace")
        else:
            context.tracing.stop()
    except PlaywrightError:
        LOGGER.exception("playwright_trace_capture_failed")
    finally:
        try:
            context.close()
        except PlaywrightError:
            LOGGER.exception("playwright_context_close_failed")


@pytest.fixture
def page(
    browser_context: BrowserContext,
    request: pytest.FixtureRequest,
) -> Generator[Page]:
    """Create a page and capture screenshot/console diagnostics on failure."""
    page_instance = browser_context.new_page()
    page_instance.on(
        "console",
        lambda message: LOGGER.info(
            "browser_console",
            extra={"type": message.type, "text": message.text},
        ),
    )
    yield page_instance

    try:
        if request.node.stash.get(UI_TEST_FAILED, False):
            if page_instance.is_closed():
                LOGGER.warning("playwright_screenshot_skipped_page_closed")
            else:
                attach_screenshot(
                    page_instance.screenshot(full_page=True),
                    name="UI failure screenshot",
                )
    except PlaywrightError:
        LOGGER.exception("playwright_screenshot_capture_failed")
    finally:
        if not page_instance.is_closed():
            try:
                page_instance.close()
            except PlaywrightError:
                LOGGER.exception("playwright_page_close_failed")
