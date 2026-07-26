"""Configuration, API, data, and Playwright fixtures."""

import logging
from collections.abc import Generator
from functools import partial

import httpx
import pytest
from faker import Faker
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Route,
    sync_playwright,
)
from playwright.sync_api import Error as PlaywrightError

from social_network_automation.api import ApiClient
from social_network_automation.api.domain import AuthClient, CommentsClient, PostsClient
from social_network_automation.api.models import AuthSession
from social_network_automation.cleanup import ResourceTracker
from social_network_automation.config import BrowserName, Settings, get_settings
from social_network_automation.data import RegistrationData, UserDataFactory
from social_network_automation.fixtures.state import UI_TEST_FAILED
from social_network_automation.reporting.allure_helpers import set_allure_parameter
from social_network_automation.reporting.artifacts import (
    artifact_stem,
    attach_screenshot,
    attach_trace,
)

LOGGER = logging.getLogger(__name__)


def _proxy_without_browser_origin(route: Route, client: httpx.Client) -> None:
    """Forward an API request without the browser Origin header."""
    headers = dict(route.request.headers)
    headers.pop("origin", None)
    headers.pop("host", None)
    response = client.request(
        route.request.method,
        route.request.url,
        headers=headers,
        content=route.request.post_data_buffer,
    )
    response_headers = dict(response.headers)
    response_headers.pop("content-encoding", None)
    response_headers.pop("content-length", None)
    response_headers.pop("transfer-encoding", None)
    route.fulfill(
        status=response.status_code,
        headers=response_headers,
        body=response.content,
    )


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


@pytest.fixture
def auth_client(api_client: ApiClient) -> AuthClient:
    """Provide authentication routes."""
    return AuthClient(api_client)


@pytest.fixture
def posts_client(api_client: ApiClient) -> PostsClient:
    """Provide post routes."""
    return PostsClient(api_client)


@pytest.fixture
def comments_client(api_client: ApiClient) -> CommentsClient:
    """Provide comment routes."""
    return CommentsClient(api_client)


@pytest.fixture
def resource_tracker(
    auth_client: AuthClient, posts_client: PostsClient
) -> Generator[ResourceTracker]:
    """Track and clean all generated API resources."""
    tracker = ResourceTracker(auth_client, posts_client)
    yield tracker
    tracker.cleanup()


@pytest.fixture
def registered_user(
    auth_client: AuthClient,
    user_data_factory: UserDataFactory,
    resource_tracker: ResourceTracker,
) -> tuple[RegistrationData, AuthSession]:
    """Create and track a unique authenticated user."""
    data = user_data_factory.registration()
    response = auth_client.register(data)
    session = AuthSession.model_validate(response.json())
    return data, resource_tracker.track(session)


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
    set_allure_parameter("browser", settings.browser.value)
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
    cors_client: httpx.Client | None = None
    if settings.cors_proxy:
        cors_client = httpx.Client(timeout=settings.api_timeout_seconds)
        context.route(
            f"{settings.api_base_url}/**",
            partial(_proxy_without_browser_origin, client=cors_client),
        )
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
        if cors_client is not None:
            cors_client.close()


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
