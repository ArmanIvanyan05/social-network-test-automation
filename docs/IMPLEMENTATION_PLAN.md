# Implementation Plan

This plan is intentionally incremental. The current SUT is not stable enough for a one-step framework build.

## Phase 0: Local application environment

### Files to create

* `pyproject.toml`
* `.gitignore`
* `.env.example`
* `README.md`
* `scripts/check_local_env.py`
* `scripts/start_frontend.ps1`
* `scripts/start_backend.ps1`
* `scripts/wait_for_url.py`
* `tests/smoke/test_frontend_health.py`
* `tests/smoke/test_backend_health.py`
* `tests/smoke/test_sut_contract.py`

### Functionality to implement

* Python project bootstrap
* dependency management
* typed environment configuration skeleton
* helpers to verify Node, npm, Docker, Mongo, frontend URL, and backend URL
* smoke checks for current SUT behavior

### Tests to add

* frontend reachable smoke test
* backend root route smoke test
* backend intended API route not mounted smoke test

### Dependencies

* Python 3.12
* pytest
* httpx
* Pydantic Settings
* Ruff
* mypy

### Risks

* local machines may not have Node or Mongo
* Docker may be installed but stopped
* backend may appear healthy via `/` while all business APIs are broken

### Completion criteria

* project installs locally
* smoke tests clearly report frontend and backend availability
* documentation explains local prerequisites and known SUT defects

### Commands that must pass

* `python -m pip install -e .[dev]`
* `ruff check .`
* `ruff format --check .`
* `mypy src`
* `pytest tests/smoke -q`

## Phase 1: Framework foundation

### Files to create

* `src/social_network_automation/config/settings.py`
* `src/social_network_automation/config/enums.py`
* `src/social_network_automation/config/urls.py`
* `src/social_network_automation/api/base_client.py`
* `src/social_network_automation/ui/browser.py`
* `src/social_network_automation/reporting/logging.py`
* `src/social_network_automation/reporting/allure_helpers.py`
* `src/social_network_automation/fixtures/env_fixtures.py`
* `src/social_network_automation/fixtures/browser_fixtures.py`
* `src/social_network_automation/fixtures/api_fixtures.py`

### Functionality to implement

* typed settings
* reusable `httpx` client setup
* Playwright browser/page lifecycle
* base diagnostics and logging
* shared pytest fixture registration

### Tests to add

* one API smoke test using base client
* one UI smoke test proving page object/browser fixture wiring

### Dependencies

* Playwright for Python
* Allure Pytest

### Risks

* unstable SUT contracts can tempt framework shortcuts
* browser startup can hide config bugs if not validated explicitly

### Completion criteria

* the framework has clean, typed foundations
* API and UI fixtures can be reused across future phases

### Commands that must pass

* `playwright install chromium`
* `ruff check .`
* `mypy src`
* `pytest tests/smoke -q`

## Phase 2: API authentication

### Files to create

* `src/social_network_automation/api/routes.py`
* `src/social_network_automation/api/auth_client.py`
* `src/social_network_automation/api/models/auth_models.py`
* `src/social_network_automation/data/factories/auth_factory.py`
* `src/social_network_automation/assertions/api_assertions.py`
* `tests/api/test_auth_api.py`

### Functionality to implement

* auth-oriented request builders
* request/response models for observed backend behavior
* tests for mounted vs missing auth routes
* negative token tests when backend auth becomes reachable

### Tests to add

* backend root health
* register/login route presence checks
* current defect checks for unmounted routes or broken handlers

### Dependencies

* stable auth route contract from SUT, or explicit defect-state assertions

### Risks

* user routes are currently broken even if mounted
* frontend and backend use incompatible auth models

### Completion criteria

* API auth tests either execute happy paths or document exact blockers
* no auth assumptions are hard-coded into unrelated parts of the framework

### Commands that must pass

* `ruff check .`
* `mypy src`
* `pytest tests/api/test_auth_api.py -q`

## Phase 3: UI authentication

### Files to create

* `src/social_network_automation/ui/pages/signup_page.py`
* `src/social_network_automation/ui/pages/login_page.py`
* `src/social_network_automation/assertions/ui_assertions.py`
* `tests/ui/test_signup_ui.py`
* `tests/ui/test_login_ui.py`

### Functionality to implement

* page objects for signup and login
* validation message handling
* navigation checks between signup and login
* defect-aware assertions around login/profile redirect behavior

### Tests to add

* signup page renders
* login page renders
* navigation between signup and login works
* profile area redirects when verification fails

### Dependencies

* Playwright fixture layer
* frontend dev server startup helper

### Risks

* successful end-to-end login is blocked by backend mismatch
* UI may render while business flow is broken

### Completion criteria

* auth UI tests are readable and stable
* blocked login success paths are documented, not silently skipped

### Commands that must pass

* `ruff check .`
* `mypy src`
* `pytest tests/ui/test_signup_ui.py tests/ui/test_login_ui.py -q`

## Phase 4: Posts and comments

### Files to create

* `src/social_network_automation/api/posts_client.py`
* `src/social_network_automation/api/models/post_models.py`
* `src/social_network_automation/api/models/comment_models.py`
* `src/social_network_automation/ui/components/gallery_component.py`
* `src/social_network_automation/ui/components/preview_modal_component.py`
* `src/social_network_automation/ui/pages/profile_page.py`
* `src/social_network_automation/data/factories/post_factory.py`
* `tests/api/test_posts_api.py`
* `tests/api/test_comments_api.py`
* `tests/ui/test_profile_ui.py`

### Functionality to implement

* API wrappers for posts/comments
* page/component objects for gallery and preview modal
* like/comment interactions
* optional defect checks for missing multipart support and route-mount failures

### Tests to add

* get posts contract tests
* post detail contract tests
* comment route contract tests
* UI gallery rendering tests

### Dependencies

* working or at least observable posts/comments routes

### Risks

* backend route modules for posts/comments currently fail to load
* frontend expects data model not produced by backend
* upload is unimplemented server-side

### Completion criteria

* posts/comments tests distinguish route-mount errors from business-rule errors
* page/component design stays modular

### Commands that must pass

* `ruff check .`
* `mypy src`
* `pytest tests/api/test_posts_api.py tests/api/test_comments_api.py -q`
* `pytest tests/ui/test_profile_ui.py -q`

## Phase 5: Follows, feed and blocking

### Files to create

* `src/social_network_automation/api/social_client.py`
* `src/social_network_automation/api/models/user_models.py`
* `src/social_network_automation/ui/pages/search_page.py`
* `tests/api/test_follows_api.py`
* `tests/api/test_blocking_api.py`
* `tests/api/test_feed_api.py`
* `tests/ui/test_search_ui.py`

### Functionality to implement

* follows/block/feed client methods
* search/account page interactions
* assertions for current placeholder or broken behavior

### Tests to add

* follow/unfollow route contract tests
* blocked route contract tests
* feed placeholder response tests
* search page render and query behavior tests

### Dependencies

* prior API foundation

### Risks

* route inputs and services are currently mismatched
* feed is a placeholder endpoint

### Completion criteria

* framework covers social graph features at least at contract level
* business-happy tests are added only where supported

### Commands that must pass

* `ruff check .`
* `mypy src`
* `pytest tests/api/test_follows_api.py tests/api/test_blocking_api.py tests/api/test_feed_api.py -q`

## Phase 6: Notifications and search

### Files to create

* `tests/api/test_notifications_api.py`
* `tests/api/test_search_api.py`
* `tests/ui/test_search_ui.py`

### Functionality to implement

* route coverage for notifications/search
* placeholder detection and defect reporting
* search UI/API correlation checks where possible

### Tests to add

* notifications list/mark-read/delete contract tests
* search users/posts contract tests

### Dependencies

* existing API fixture and model layer

### Risks

* current backend endpoints are placeholders only

### Completion criteria

* route behavior is documented by executable tests

### Commands that must pass

* `ruff check .`
* `mypy src`
* `pytest tests/api/test_notifications_api.py tests/api/test_search_api.py -q`

## Phase 7: Database and Redis validation

### Files to create

* `src/social_network_automation/db/mongo_client.py`
* `src/social_network_automation/db/mongo_queries.py`
* `src/social_network_automation/db/redis_client.py`
* `src/social_network_automation/assertions/db_assertions.py`
* `tests/api/test_db_validation.py`

### Functionality to implement

* optional MongoDB connection layer
* safe read-only queries for users/posts/comments
* Redis connection layer behind feature flag

### Tests to add

* user password hashing validation
* post/comment persistence validation
* Redis tests only if real Redis-backed features exist

### Dependencies

* MongoDB availability
* confirmed feature flows that actually persist data

### Risks

* Redis is currently unused by the SUT
* over-coupling tests to DB schema can create brittle suites

### Completion criteria

* Mongo validation is optional and reliable
* Redis validation remains opt-in and may legitimately have zero active tests

### Commands that must pass

* `ruff check .`
* `mypy src`
* `pytest tests/api/test_db_validation.py -q`

## Phase 8: End-to-end workflows

### Files to create

* `tests/e2e/test_authentication_flow.py`
* `tests/e2e/test_post_comment_flow.py`
* `tests/e2e/test_follow_block_flow.py`

### Functionality to implement

* cross-layer user journeys
* API setup + UI validation combinations
* optional DB verification after workflows

### Tests to add

* auth flow
* post/comment flow
* follow/block flow

### Dependencies

* stable auth
* stable CRUD behavior
* stable selectors

### Risks

* these flows are currently blocked by SUT contract mismatches

### Completion criteria

* at least one end-to-end path runs green from setup to cleanup

### Commands that must pass

* `ruff check .`
* `mypy src`
* `pytest tests/e2e -q`

## Phase 9: Docker

### Files to create

* `Dockerfile`
* `docker-compose.yml`
* `scripts/docker_run.ps1`

### Functionality to implement

* containerized automation execution
* optional Mongo/Redis services for local automation runs
* documented way to point containers at locally running frontend/backend or containerized SUT services later

### Tests to add

* container smoke run of automation suite

### Dependencies

* Docker Desktop running

### Risks

* the SUT repos currently contain no Docker assets
* frontend/backend startup may need custom scripting inside compose

### Completion criteria

* automation suite runs in Docker for at least smoke tests

### Commands that must pass

* `docker compose up --build --abort-on-container-exit`

## Phase 10: GitHub Actions and Allure reporting

### Files to create

* `.github/workflows/ci.yml`
* `scripts/publish_allure.ps1` or equivalent helper if needed

### Functionality to implement

* lint/type/test workflow
* artifact upload for screenshots, traces, and Allure results
* matrix strategy if smoke/api/ui jobs need separation

### Tests to add

* CI itself becomes the validation target here

### Dependencies

* stable local commands from prior phases

### Risks

* CI environment may not support full browser or SUT startup without extra setup

### Completion criteria

* PR-ready CI job exists
* Allure results are preserved as artifacts

### Commands that must pass

* local equivalent of CI command chain:
  * `ruff check .`
  * `mypy src`
  * `pytest -m smoke -q`

## Phase 11: Documentation and final code review

### Files to create

* final updates to `README.md`
* final updates to all files in `docs/`

### Functionality to implement

* installation and execution instructions
* marker reference
* troubleshooting section
* final architecture cleanup

### Tests to add

* no new placeholder tests
* only targeted coverage added if review reveals gaps

### Dependencies

* all prior phases substantially complete

### Risks

* documentation can lag behind real commands if not verified line by line

### Completion criteria

* docs match the repository exactly
* duplicate utilities are removed
* final framework commands are reproducible

### Commands that must pass

* `ruff check .`
* `ruff format --check .`
* `mypy src`
* `pytest -q`
