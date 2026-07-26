"""Frontend loading smoke coverage."""

import pytest
from playwright.sync_api import Page, expect

from social_network_automation.config import Settings
from social_network_automation.reporting.allure_helpers import set_allure_labels


@pytest.mark.smoke
@pytest.mark.ui
def test_frontend_loads_registration_page(page: Page, settings: Settings) -> None:
    """Verify a fresh browser context renders the registration entrypoint."""
    set_allure_labels(feature="Environment", story="Frontend loading")
    response = page.goto(settings.frontend_base_url, wait_until="domcontentloaded")

    assert response is not None
    assert response.ok
    expect(page.get_by_role("heading", name="Create account")).to_be_visible()
