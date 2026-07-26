# Social Network Test Automation

Portfolio-ready Python automation for the verified authentication, session,
posts, and comments vertical slices of a React/Express social network.

The project exercises the public application contracts through REST, browser,
and hybrid API/UI workflows. It deliberately excludes unfinished social
features instead of encoding invented requirements.

## System under test

| Service | Default address | Role |
| --- | --- | --- |
| React/Vite frontend | `http://localhost:5173` | Browser UI |
| Express API | `http://localhost:4002/api` | REST interface |
| MongoDB 7 | `127.0.0.1:27017` | Backend persistence |

The backend must return HTTP 200 and `database: connected` from
`GET /api/health`. Environment variables can point the framework at another
local or CI deployment.

## Architecture and stack

Python 3.12, pytest, synchronous Playwright, httpx, Pydantic Settings, Faker,
Allure Pytest, pytest-xdist, Ruff, mypy, pre-commit, Docker, and GitHub Actions
form the toolchain.

```text
.
|-- .github/workflows/tests.yml
|-- Dockerfile
|-- conftest.py
|-- pyproject.toml
|-- src/social_network_automation/
|   |-- api/          # transport, domain clients, and typed payload models
|   |-- config/       # validated environment settings
|   |-- data/         # unique Faker-backed identities
|   |-- fixtures/     # API, cleanup, and Playwright lifecycles
|   |-- reporting/    # redacted Allure attachments and JSON logging
|   |-- ui/           # focused page/component interactions
|   |-- assertions.py # reusable business-neutral response checks
|   `-- cleanup.py    # visible API cleanup with no development DB access
|-- tests/
|   |-- api/
|   |-- ui/
|   |-- e2e/
|   `-- smoke/
`-- docs/
    |-- TEST_COVERAGE.md
    `-- FINAL_REPORT.md
```

Clients communicate but do not assert. Page objects expose interactions but
not complete scenarios. Tests own business assertions. Each test creates a
unique user and the teardown tracker removes that user's posts, comments
(through post deletion), and profile through supported APIs.

## Prerequisites and installation

- CPython 3.12
- Node.js 20 or newer and npm
- Docker Desktop, or a compatible local MongoDB 7
- Allure CLI only for rendering reports

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m playwright install chromium firefox webkit
```

Create local configuration without committing it:

```powershell
Copy-Item .env.example .env
```

| Variable | Default | Meaning |
| --- | --- | --- |
| `AUTOMATION_ENVIRONMENT` | `local` | Environment label |
| `AUTOMATION_FRONTEND_URL` | `http://localhost:5173` | UI origin |
| `AUTOMATION_API_URL` | `http://localhost:4002/api` | API base |
| `AUTOMATION_BROWSER` | `chromium` | Chromium, Firefox, or WebKit |
| `AUTOMATION_HEADLESS` | `true` | Headless browser mode |
| `AUTOMATION_SLOW_MO_MS` | `0` | Optional local action delay |
| `AUTOMATION_UI_TIMEOUT_MS` | `10000` | Locator timeout |
| `AUTOMATION_API_TIMEOUT_SECONDS` | `10` | HTTP timeout |
| `AUTOMATION_IGNORE_HTTPS_ERRORS` | `false` | Browser TLS behavior |
| `AUTOMATION_CORS_PROXY` | `false` | Explicit local CORS workaround |
| `AUTOMATION_ARTIFACTS_DIR` | `artifacts` | Failure diagnostics |

`AUTOMATION_CORS_PROXY=true` removes the browser Origin header only from
framework-forwarded API traffic. It is intended solely for a local frontend
port that is not in the running backend's CORS configuration. Keep it false in
normal local and CI environments so CORS remains part of the tested contract.

Never place passwords, JWTs, personal information, or database credentials in
the committed configuration.

## Start the application

MongoDB and backend:

```powershell
cd ..\social-network-advanced-backend
docker compose up -d mongodb
Copy-Item .env.example .env  # first run only; replace JWT_SECRET locally
npm ci
npm start
```

The backend development database is configured in its `.env`. Backend-owned
integration tests use `social_network_test`; this automation never manipulates
either database directly.

Frontend in a second terminal:

```powershell
cd ..\social-app
npm ci
$env:VITE_API_BASE_URL = "http://localhost:4002/api"
npm run dev -- --host 127.0.0.1 --port 5173
```

Verify both services:

```powershell
Invoke-RestMethod http://localhost:4002/api/health
Invoke-WebRequest -UseBasicParsing http://localhost:5173
```

The frontend origin must exactly match the backend `FRONTEND_ORIGIN`. If Vite
selects port 5174 because 5173 is occupied, either restart it with a fixed
allowed port or update the backend environment and restart the backend. The
explicit proxy setting above is a test-runner workaround, not a production
configuration.

## Running tests

```powershell
# availability
python -m pytest tests\smoke -v

# REST regression, including auth/authorization
python -m pytest tests\api -v

# parallel-safe REST execution
python -m pytest tests\api -n 2 -v

# browser regression and hybrid workflows
python -m pytest tests\ui -v
python -m pytest tests\e2e -v

# useful marker selections
python -m pytest -m "smoke"
python -m pytest -m "api and auth"
python -m pytest -m "regression and not e2e"
```

Markers are `smoke`, `regression`, `api`, `ui`, `e2e`, `auth`, `database`,
and `serial`. Database and serial are registered for planned, explicit use;
the v1 suite does not directly query MongoDB.

Browser and headed-mode examples:

```powershell
$env:AUTOMATION_BROWSER = "firefox"
$env:AUTOMATION_HEADLESS = "false"
python -m pytest tests\ui -m smoke -v
```

The main UI regression runs once with configured Chromium by default. Run only
critical authentication smoke cases on all three browser engines:

```powershell
foreach ($browser in "chromium", "firefox", "webkit") {
  $env:AUTOMATION_BROWSER = $browser
  python -m pytest tests\ui\test_auth_ui.py -m smoke -v
}
```

## Quality and reports

```powershell
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest --collect-only -q
python -m pre_commit run --all-files
```

Generate and view Allure results:

```powershell
python -m pytest --alluredir=allure-results
allure serve allure-results
```

API attachments redact passwords, tokens, authorization headers, and cookies.
Failed UI tests attach an in-memory full-page PNG and preserve a Playwright
trace under `artifacts/`; passing traces are discarded.

## Docker

The image uses the Playwright Python base matching the installed Playwright
release. It copies no `.env`, virtual environment, browser cache, or generated
report.

```powershell
docker build -t social-network-automation .
docker run --rm `
  -e AUTOMATION_FRONTEND_URL=http://host.docker.internal:5173 `
  -e AUTOMATION_API_URL=http://host.docker.internal:4002/api `
  -v "${PWD}\allure-results:/automation/allure-results" `
  social-network-automation tests\smoke -v --alluredir=allure-results
```

Use container-reachable service names instead of `host.docker.internal` when
running all services on one Compose network.

## GitHub Actions

The pull-request/manual workflow checks out this repository plus the backend
and frontend, provisions healthy MongoDB 7, generates an ephemeral JWT signing
key, starts both applications on fixed ports, waits with bounded loops, and
runs static checks, collection, API tests, smoke tests, and selected Chromium
UI/E2E coverage. It uses `social_network_ci_test`, never the development
database. Allure data, traces, screenshots, service logs, and pytest logs are
uploaded even on failure.

## Supported scope and limitations

Supported: registration, login, Bearer sessions, current user, post CRUD,
comment CRUD, validation, missing/malformed credentials, missing resources,
and ownership enforcement.

Out of scope because the verified product slices do not support them: feed,
follows, blocking, notifications, chat, likes, media upload, privacy settings,
and social-graph behavior.

See [docs/TEST_COVERAGE.md](docs/TEST_COVERAGE.md) for the coverage map and
[docs/FINAL_REPORT.md](docs/FINAL_REPORT.md) for the latest verified execution.

## Troubleshooting

- Backend unavailable: call `/api/health`, check port 4002 and MongoDB health,
  then inspect backend logs. Tests fail rather than pretending an unavailable
  SUT passed.
- Frontend unavailable: check the configured URL and Vite output. Port 5174 is
  valid only when the backend CORS origin matches it (or the documented local
  proxy is explicitly enabled).
- Browser missing: run `python -m playwright install chromium firefox webkit`.
- Trace inspection: run
  `python -m playwright show-trace artifacts\<trace-name>.zip`.
- Cleanup failure: pytest reports teardown as failed. Remove the generated
  resources through the supported API after restoring service availability.
