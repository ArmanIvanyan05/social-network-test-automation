# Test Coverage

## Covered functionality

The v1 suite covers the verified authentication, session, posts, and comments
contracts.

| Layer | Positive coverage | Negative and authorization coverage |
| --- | --- | --- |
| API authentication | register, login, current user, profile, full auth flow | duplicates, missing/invalid values, bad credentials, missing/malformed/invalid token, malformed user ID, password-field leakage |
| API posts | create, read, list, update, delete, CRUD flow | empty content, missing auth, malformed/missing IDs, cross-user update/delete, password-field leakage |
| API comments | create, list, update, delete, lifecycle flow | empty content, missing auth, malformed/missing IDs, missing parent, cross-user update/delete |
| UI authentication | register, login, reload restoration, logout | bad credentials, protected-route redirect, public-only redirect, required fields |
| UI posts/comments | create, display, edit, delete | empty post and comment validation |
| Hybrid E2E | API user to UI session; API post to UI edit to API verification; UI registration/post/comment to API verification | session boundary and cleanup behavior |
| Smoke | backend database health, frontend loading, critical auth UI/E2E | service availability |

The suite uses unique Faker data and API cleanup. API tests are designed for
two-worker xdist execution. The primary UI regression targets configured
Chromium; critical authentication smoke coverage is also executable on Firefox
and WebKit.

## Important contract checks

- Exact HTTP status and stable backend error codes.
- Response envelopes and typed important fields.
- Standard `Authorization: Bearer <token>` behavior.
- No password or password-hash key in auth, profile, post, or author payloads.
- Post/comment ownership returns stable 403 errors.
- Malformed IDs return stable 400 errors; missing resources return stable 404
  errors.
- Browser session persistence uses the actual frontend local-storage contract.
- UI actions are verified through visible state and, in E2E cases, API reads.

## Out of scope

Feed, follows, blocking, notifications, chat, Redis behavior, likes, media
upload, privacy/settings, and social-graph workflows are not part of the
verified v1 product slice and are intentionally not tested.

## Known limitations

- Cleanup uses supported API deletion. If the SUT becomes unavailable during
  teardown, cleanup is reported as an error and may require later API cleanup.
- The framework performs no direct MongoDB deletion. This avoids accidental
  development database damage.
- A frontend served from port 5174 cannot make browser API calls when the
  backend allows only port 5173. `AUTOMATION_CORS_PROXY=true` is an explicit
  local-only request-forwarding workaround; CI uses matching port 5173.
- Direct accessibility labels from MDB authentication inputs are not correctly
  associated in the current HTML. Those inputs use stable `name` attributes;
  other controls use accessible roles, names, and labels.
- Cross-browser behavior depends on installed Playwright browser binaries and
  the external SUT being available.
