# Test Strategy

## Goal

Build a professional Python automation framework that can test the social network application at three levels:

* UI
* API
* end-to-end UI + API + optional DB validation

The strategy must reflect current reality:

* the frontend is partially runnable
* the backend entrypoint runs, but its real API surface is not exposed
* many backend features are placeholders or structurally broken

## Strategy principles

1. Test what is real today, not what filenames imply.
2. Separate SUT defects from automation defects.
3. Start with environment verification and contract smoke checks.
4. Prefer API-based setup/cleanup when the backend contract becomes reliable.
5. Keep database and Redis validation optional and configuration-driven.
6. Mark blocked scenarios explicitly with source-backed reasons.

## Test pyramid for this project

### Layer 1: environment and contract smoke checks

Purpose:

* prove that frontend, backend, MongoDB, and optional Redis are reachable
* detect port/config/auth mismatches immediately
* fail fast when the SUT is not runnable

Examples:

* frontend base URL reachable
* backend root route reachable
* expected API endpoints mounted
* Mongo connection available
* JWT secret configured

### Layer 2: API tests

Purpose:

* validate request/response contracts directly
* set up test data quickly
* isolate backend logic from UI

Important constraint:

The backend is not ready for broad API automation yet. Initial API coverage should focus on:

* health checks
* auth contract discovery
* negative tests that prove broken or missing routes
* service-level behavioral expectations once routes are repaired

### Layer 3: UI tests

Purpose:

* validate user-visible flows
* verify navigation, forms, error states, and content rendering

Important constraint:

UI tests must be split into:

* UI-only shell tests that prove routing/pages render
* integrated tests that require a working backend

### Layer 4: end-to-end tests

Purpose:

* verify complete workflows across frontend, backend, and persistence layers

Examples:

* register -> login -> create post -> comment -> verify DB state
* follow -> feed update -> block -> verify visibility rules

Important constraint:

These should be enabled only after contract alignment and backend repair.

## Recommended test suites

### `smoke`

Run on every local change and in CI:

* environment checks
* backend health
* frontend startup
* route-mount verification

### `api`

Run once auth and core CRUD routes are stable:

* authentication
* posts/comments
* follows/blocking
* notifications/search
* settings/media where implemented

### `ui`

Run against stable frontend + backend integration:

* signup/login
* profile navigation
* search
* post creation
* commenting
* follow/unfollow flows

### `e2e`

Run after API and UI layers are both stable:

* end-to-end user journeys with optional Mongo validation

### `negative`

Always important for this project:

* missing token
* invalid token
* unauthorized edit/delete
* invalid route wiring
* unsupported upload behavior

## Environment matrix

Minimum supported environments for the automation framework:

| Environment | Purpose |
| --- | --- |
| `local` | developer machine with local or Dockerized dependencies |
| `ci` | GitHub Actions |

Optional future environments:

* `docker-local`
* `staging`, if the SUT later gains a deployable hosted environment

## Data strategy

### Preferred approach

* create fresh users dynamically
* create and clean test data through API clients
* isolate data per test where practical
* use unique Faker-generated identities

### Current limitation

Because the backend contract is broken, Phase 0 and Phase 1 should not assume working business APIs.

Until auth and CRUD are repaired:

* use smoke tests and route-contract checks
* avoid large suites that depend on user creation via backend API

## Assertions strategy

Keep assertions close to business behavior:

* API clients return typed responses only
* page objects perform interactions only
* assertion helpers validate domain outcomes

Examples:

* `assert_user_is_logged_in(page)`
* `assert_post_visible(page, text)`
* `assert_status_code(response, 401)`

## Database and Redis validation strategy

### MongoDB

Use optional Mongo assertions for:

* user creation
* password hashing verification
* post/comment persistence
* follow/block persistence
* cleanup verification

### Redis

Current backend code does not use Redis. Therefore:

* do not add mandatory Redis tests initially
* keep Redis utilities behind feature flags
* add Redis assertions only when SUT code actually creates Redis state

## Diagnostics strategy

For failed UI tests capture:

* screenshot
* Playwright trace
* console logs when relevant
* network request failures when relevant

For failed API tests capture:

* full request method/path
* sanitized headers
* request body
* response status/body
* structured logs

For failed DB checks capture:

* query used
* matched documents count
* sanitized document snapshot

## Coverage priorities

### Priority 1

* local environment verification
* frontend startup verification
* backend startup verification
* route mounting and auth contract smoke tests

### Priority 2

* API authentication
* UI authentication
* posts/comments

### Priority 3

* follows/feed/blocking
* notifications/search
* optional DB checks

### Priority 4

* media
* settings
* chat
* Redis checks, only if SUT adds real Redis behavior

## What should be treated as blocked at framework start

The following should be documented as blocked until the SUT changes:

* full frontend-backend end-to-end auth
* file upload end to end
* mounted post/comment APIs
* route-level JWT auth verification through the running backend
* notification/search/chat/media workflows as business features

## Exit criteria for the first usable automation version

The framework is ready for real feature automation when all of the following are true:

1. environment smoke suite passes locally
2. backend exposes mounted auth routes
3. frontend and backend share the same base URL/port strategy
4. auth mechanism is consistent between UI and API
5. at least one vertical slice is fully testable:
   * create user
   * login
   * create post
   * verify post in UI or DB
