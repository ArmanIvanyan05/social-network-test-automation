# Automation Architecture

## Objective

Create a Python 3.12 test automation framework in `social-network-test-automation` that is:

* readable
* strongly typed
* easy to extend by feature
* suitable for UI, API, and end-to-end testing
* able to document blocked SUT behavior without hiding failures

## Design principles

1. Keep configuration centralized and typed.
2. Keep UI interaction separate from assertions.
3. Keep API communication separate from test expectations.
4. Organize tests by business domain, not by tool.
5. Prefer fixtures and factories over shared static data.
6. Make Mongo and Redis checks optional.
7. Preserve strong failure diagnostics.

## Proposed project layout

```text
social-network-test-automation/
├─ .env.example
├─ .gitignore
├─ .pre-commit-config.yaml
├─ Dockerfile
├─ README.md
├─ pyproject.toml
├─ pytest.ini
├─ docs/
│  ├─ ARCHITECTURE.md
│  ├─ IMPLEMENTATION_PLAN.md
│  ├─ KNOWN_ISSUES.md
│  ├─ SUT_ANALYSIS.md
│  └─ TEST_STRATEGY.md
├─ scripts/
│  ├─ check_local_env.py
│  ├─ start_backend.ps1
│  ├─ start_frontend.ps1
│  └─ wait_for_url.py
├─ src/
│  └─ social_network_automation/
│     ├─ __init__.py
│     ├─ config/
│     │  ├─ __init__.py
│     │  ├─ enums.py
│     │  ├─ settings.py
│     │  └─ urls.py
│     ├─ api/
│     │  ├─ __init__.py
│     │  ├─ auth_client.py
│     │  ├─ posts_client.py
│     │  ├─ social_client.py
│     │  ├─ base_client.py
│     │  ├─ routes.py
│     │  └─ models/
│     │     ├─ __init__.py
│     │     ├─ auth_models.py
│     │     ├─ comment_models.py
│     │     ├─ common.py
│     │     ├─ post_models.py
│     │     └─ user_models.py
│     ├─ ui/
│     │  ├─ __init__.py
│     │  ├─ pages/
│     │  │  ├─ login_page.py
│     │  │  ├─ profile_page.py
│     │  │  ├─ search_page.py
│     │  │  ├─ settings_page.py
│     │  │  └─ signup_page.py
│     │  ├─ components/
│     │  │  ├─ gallery_component.py
│     │  │  ├─ nav_bar_component.py
│     │  │  └─ preview_modal_component.py
│     │  └─ browser.py
│     ├─ assertions/
│     │  ├─ __init__.py
│     │  ├─ api_assertions.py
│     │  ├─ db_assertions.py
│     │  └─ ui_assertions.py
│     ├─ data/
│     │  ├─ __init__.py
│     │  ├─ factories/
│     │  │  ├─ auth_factory.py
│     │  │  ├─ post_factory.py
│     │  │  └─ user_factory.py
│     │  └─ payload_builders.py
│     ├─ db/
│     │  ├─ __init__.py
│     │  ├─ mongo_client.py
│     │  ├─ mongo_queries.py
│     │  └─ redis_client.py
│     ├─ fixtures/
│     │  ├─ __init__.py
│     │  ├─ api_fixtures.py
│     │  ├─ browser_fixtures.py
│     │  ├─ data_fixtures.py
│     │  ├─ env_fixtures.py
│     │  └─ sut_fixtures.py
│     ├─ reporting/
│     │  ├─ __init__.py
│     │  ├─ allure_helpers.py
│     │  └─ logging.py
│     └─ utils/
│        ├─ __init__.py
│        ├─ polling.py
│        ├─ process.py
│        └─ timeouts.py
├─ tests/
│  ├─ api/
│  │  ├─ test_auth_api.py
│  │  ├─ test_comments_api.py
│  │  ├─ test_posts_api.py
│  │  └─ test_route_contracts.py
│  ├─ e2e/
│  │  ├─ test_authentication_flow.py
│  │  └─ test_post_comment_flow.py
│  ├─ smoke/
│  │  ├─ test_backend_health.py
│  │  ├─ test_frontend_health.py
│  │  └─ test_sut_contract.py
│  └─ ui/
│     ├─ test_login_ui.py
│     ├─ test_profile_ui.py
│     ├─ test_search_ui.py
│     └─ test_signup_ui.py
└─ artifacts/
   ├─ .gitkeep
   └─ .gitignore
```

## Layer responsibilities

## `config`

Responsibilities:

* read environment variables with Pydantic Settings
* define URLs, ports, timeouts, browser options, DB toggles
* separate `local` and `ci` behavior

Key rule:

No test should read environment variables directly.

## `api`

Responsibilities:

* build request URLs
* send HTTP requests with `httpx`
* deserialize responses into typed models where possible
* expose domain clients by feature

Key rule:

API clients do not contain assertions.

## `ui/pages` and `ui/components`

Responsibilities:

* page objects model screens
* components model reusable screen fragments
* expose locators and interactions only

Key rule:

Assertions stay in tests or assertion helpers.

## `data/factories`

Responsibilities:

* generate unique users, posts, comments, and search inputs
* centralize defaults and overrides

Key rule:

Factories should be deterministic enough for debugging and random enough to avoid collisions.

## `db`

Responsibilities:

* optional MongoDB and Redis access
* read-only verification helpers by default
* safe cleanup helpers when explicitly enabled

Key rule:

DB helpers must be optional and guarded by configuration.

## `fixtures`

Responsibilities:

* browser lifecycle
* API client instances
* SUT reachability checks
* environment bootstrapping
* data cleanup hooks

Key rule:

Fixtures should compose small concerns instead of building one large global fixture.

## `assertions`

Responsibilities:

* domain-specific readable checks
* better error messages than raw `assert response.status_code == ...`

Examples:

* `assert_user_profile_loaded(...)`
* `assert_post_created(...)`
* `assert_route_is_missing(...)`

## `reporting`

Responsibilities:

* Allure attachments
* structured logs
* screenshot/trace attachment helpers

## Test organization

Tests should be organized by both level and business domain:

* `tests/smoke` for startup and contract validation
* `tests/api` for direct HTTP checks
* `tests/ui` for browser-only workflows
* `tests/e2e` for combined scenarios

This structure keeps collection predictable and supports targeted CI jobs.

## Environment model

Recommended settings model:

* `environment`
* `frontend_url`
* `backend_url`
* `mongo_uri`
* `redis_url`
* `headless`
* `slow_mo_ms`
* `browser_name`
* `api_timeout_seconds`
* `ui_timeout_ms`
* `capture_trace_on_failure`
* `capture_console_on_failure`

## Markers

Recommended pytest markers:

* `smoke`
* `api`
* `ui`
* `e2e`
* `db`
* `redis`
* `negative`
* `auth`
* `posts`
* `comments`
* `follows`
* `search`

## Handling the current SUT instability

The framework should explicitly support two classes of tests:

### Executable business tests

These validate working features.

### Contract and defect tests

These validate current broken behavior without pretending it is correct.

Examples:

* backend root health is reachable
* `/api/users/register` is not mounted in the running backend
* frontend build currently fails
* file upload endpoint is unimplemented

This is important because the current application is not feature-complete enough for a pure happy-path framework.

## First implementation boundary

The initial framework version should not attempt every final feature. It should first prove:

1. typed configuration works
2. browser and API clients work
3. SUT startup probes work
4. diagnostics are captured
5. smoke tests can distinguish environment failures from SUT failures
