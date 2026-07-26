# Social Network Test Automation

Production-style Python test automation for the verified social network
frontend and backend. The current foundation supplies typed configuration,
synchronous Playwright fixtures, a reusable `httpx` client, generated data,
structured logging, Allure diagnostics, and executable environment smoke tests.

Full authentication, post, and comment suites are intentionally deferred to
later implementation phases.

## System under test

| Service | Default URL | Purpose |
| --- | --- | --- |
| React frontend | `http://localhost:5173` | Browser UI |
| Express API | `http://localhost:4002/api` | REST API |
| MongoDB | `mongodb://127.0.0.1:27017/social_network` | Backend persistence |

The backend health contract is:

```http
GET /api/health
```

The smoke test requires HTTP 200 and a JSON response reporting
`database: connected`.

## Architecture

```text
.
├── conftest.py
├── pyproject.toml
├── src/social_network_automation/
│   ├── api/          # synchronous HTTP transport, no test assertions
│   ├── config/       # Pydantic Settings and browser enum
│   ├── data/         # Faker-backed unique data factories
│   ├── fixtures/     # API and Playwright lifecycle fixtures
│   └── reporting/    # JSON logs and Allure attachments
└── tests/
    └── smoke/        # executable API and UI availability checks
```

The package uses a `src` layout so tests exercise the installed package. API
clients only perform communication. Assertions remain in tests. Browser,
context, and page fixtures are separate so later tests can override the
smallest necessary lifecycle.

## Prerequisites

- Python 3.12
- Node.js and npm for both SUT repositories
- Docker Desktop or another reachable MongoDB 7 installation
- Allure CLI only when serving a local HTML report

Verify Python before installing:

```powershell
py -3.12 --version
```

## Install

From `social-network-test-automation`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m playwright install chromium firefox webkit
```

Only install a single browser when disk or CI time is constrained:

```powershell
python -m playwright install chromium
```

## Environment configuration

Copy the safe example and adjust local values:

```powershell
Copy-Item .env.example .env
```

Supported variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `AUTOMATION_ENVIRONMENT` | `local` | Environment label |
| `AUTOMATION_FRONTEND_URL` | `http://localhost:5173` | Frontend origin |
| `AUTOMATION_API_URL` | `http://localhost:4002/api` | API base URL |
| `AUTOMATION_BROWSER` | `chromium` | `chromium`, `firefox`, or `webkit` |
| `AUTOMATION_HEADLESS` | `true` | Headless browser execution |
| `AUTOMATION_SLOW_MO_MS` | `0` | Playwright action delay |
| `AUTOMATION_UI_TIMEOUT_MS` | `10000` | Playwright locator timeout |
| `AUTOMATION_API_TIMEOUT_SECONDS` | `10` | HTTP request timeout |
| `AUTOMATION_IGNORE_HTTPS_ERRORS` | `false` | Ignore browser TLS errors |
| `AUTOMATION_ARTIFACTS_DIR` | `artifacts` | Failure artifact directory |

Never put real passwords, JWTs, or personal data in `.env`.

## Start the local SUT

Start MongoDB from the backend repository:

```powershell
cd ..\social-network-advanced-backend
docker compose up -d mongodb
docker compose ps
```

Create a backend `.env` from its safe example, set a local-only
`JWT_SECRET`, then start it:

```powershell
npm install
npm start
```

In another terminal, start the frontend:

```powershell
cd ..\social-app
npm install
npm run dev
```

Confirm the backend before running smoke tests:

```powershell
Invoke-RestMethod http://localhost:4002/api/health
```

## Run tests

All tests:

```powershell
pytest
```

Smoke tests:

```powershell
pytest tests/smoke -v
```

API or UI only:

```powershell
pytest -m api
pytest -m ui
```

Select a browser:

```powershell
$env:AUTOMATION_BROWSER = "firefox"
pytest -m ui
```

Run headed:

```powershell
$env:AUTOMATION_HEADLESS = "false"
pytest -m ui
```

Parallel execution:

```powershell
pytest -n auto -m "not serial"
pytest -m serial
```

The `serial` marker identifies tests that must be scheduled separately. The
foundation smoke tests are parallel-safe.

## Markers

- `smoke` — critical availability checks
- `regression` — broad regression coverage
- `api` — direct REST coverage
- `ui` — browser coverage
- `e2e` — cross-layer workflows
- `auth` — authentication and authorization
- `database` — direct database validation
- `serial` — isolated scheduling required

## Quality checks

```powershell
ruff check .
ruff format --check .
mypy
pytest --collect-only -q
pre-commit run --all-files
```

Install the local Git hook after dependency installation:

```powershell
pre-commit install
```

## Allure reporting and diagnostics

Write Allure results:

```powershell
pytest --alluredir=allure-results
allure serve allure-results
```

For failed UI tests the framework:

1. captures a full-page PNG screenshot;
2. saves a Playwright trace containing screenshots, snapshots, and sources;
3. attaches both to Allure;
4. emits browser console messages through structured JSON logging.

Successful UI tests discard their trace. Generated diagnostics are ignored by
Git.

## CI and Docker execution

The framework is prepared for CI configuration through environment variables
and headless execution. A later phase will add GitHub Actions and a framework
Docker image. Until then, CI should:

1. provision MongoDB;
2. start the backend and wait for `/api/health`;
3. start the frontend and wait for `/`;
4. install Python dependencies and Playwright browsers;
5. run Ruff, mypy, collection, and smoke tests;
6. preserve `allure-results` and failure artifacts.

Do not claim Docker-based framework execution until that later phase supplies
and verifies its Dockerfile.

## Troubleshooting

### Python 3.12 is not found

Install CPython 3.12 and reopen the terminal. `py -0p` should list the
interpreter. A Microsoft Store alias without an installed interpreter is not
sufficient.

### Browser executable is missing

```powershell
python -m playwright install chromium firefox webkit
```

### Backend smoke test fails

Check:

```powershell
Invoke-RestMethod http://localhost:4002/api/health
```

The test intentionally fails when MongoDB is not reported as connected.

### Frontend smoke test fails

Confirm `npm run dev` is running at the configured URL and that the page shows
the accessible `Create account` heading in a fresh browser context.

### View a failed Playwright trace

```powershell
python -m playwright show-trace artifacts\<trace-file>.zip
```
