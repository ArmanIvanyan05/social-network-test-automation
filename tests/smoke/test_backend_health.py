"""Backend availability smoke coverage."""

import pytest

from social_network_automation.api import ApiClient
from social_network_automation.reporting.allure_helpers import set_allure_labels


@pytest.mark.smoke
@pytest.mark.api
def test_backend_health_reports_connected_database(api_client: ApiClient) -> None:
    """Verify the backend and its MongoDB dependency are ready."""
    set_allure_labels(feature="Environment", story="Backend health")
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "social-network-advanced-backend",
        "database": "connected",
    }
