# Known Issues

Investigation date: July 25, 2026

## Critical blockers

### 1. Frontend and backend do not share the same contract

Evidence:

* frontend base URL is hard-coded to `http://localhost:4002`
* backend listens on `5001` by default
* frontend expects cookie-based auth
* backend expects raw JWT in `Authorization`
* frontend paths and payloads do not match backend paths and payloads

Impact:

* successful end-to-end auth is blocked
* API-assisted UI setup is blocked
* most feature tests cannot be green end to end

### 2. Backend does not mount its route modules

Evidence:

* `app.js` exposes only `GET /`
* `POST /api/users/register` returned `404`

Impact:

* all business API tests are blocked against the running backend

### 3. `middleware/auth.js` is corrupted

Evidence:

* route module loading for `posts` and `comment` throws `SyntaxError: Identifier 'authMiddleware' has already been declared`
* the file contains middleware code plus appended route code

Impact:

* posts/comment route modules cannot even be imported

### 4. `routes/user.js` imports services incorrectly

Evidence:

* register/login handlers return `registerUser is not a function` and `loginUser is not a function` when invoked

Impact:

* user auth/profile routes are unusable even if they are mounted

### 5. File upload is not implemented server-side

Evidence:

* frontend submits multipart `FormData`
* backend only registers `bodyParser` for JSON/urlencoded requests
* no upload middleware or storage layer exists

Impact:

* profile image upload and post media upload cannot work end to end

## Major defects

### 6. Frontend production build fails

Evidence:

* `npm run build` fails on TypeScript errors in `Preview.tsx`, `Gallery.tsx`, `Profile/dashboard`, `Account`, `Followers`, `Followings`, and `Requests`

Impact:

* the frontend is not in a releasable state
* strict CI for the frontend would fail immediately

### 7. Backend delete services use removed Mongoose API

Evidence:

* `user.remove`, `post.remove`, and `comment.remove` are `undefined` under Mongoose 8

Impact:

* delete user/post/comment flows will fail if reached

### 8. Mongoose reference names are inconsistent

Evidence:

* user model name is `User`
* post model name is `posts`
* comment model name is `Comment`
* post refs use `users`
* comment post ref uses `Post`

Impact:

* population behavior is unreliable or broken
* DB assertions must be written carefully

### 9. Follows and blocks logic is incomplete

Evidence:

* routes use `req.user` without auth middleware
* unfollow/unblock filter results are not assigned
* follow service never updates `followings`
* blocked list route calls the wrong service method

Impact:

* social graph behavior is unreliable even if routes are mounted

### 10. Search, feed, notifications, chat, media, and settings are placeholders

Evidence:

* source returns static success messages without persistence or service logic

Impact:

* feature-complete automation is not possible for those domains yet

## Moderate issues

### 11. Frontend profile dashboard triggers requests during render

Evidence:

* `getAllFollowers()` and `getAllFollowings()` are called directly in component body

Impact:

* repeated requests
* flaky UI behavior
* noisy network logs during test execution

### 12. Accessibility and selector quality are mixed

Evidence:

* several interactions use clickable images instead of semantic buttons
* there are no test IDs

Impact:

* UI automation can still work, but locator resilience is lower than ideal

### 13. No Docker assets are provided by the SUT repos

Evidence:

* no `Dockerfile`
* no compose file

Impact:

* containerized SUT startup must be invented in the automation repo later

## Environmental observations

### 14. Python 3.12 is not installed or available on `PATH`

Impact:

* the required Python automation stack cannot yet be installed or executed

Mitigation:

* install Python 3.12 before Phase 0 and keep explicit environment checks
* standardize frontend/backend execution on Node 20 LTS even though the current
  machine's Node `v24.18.0` and npm `11.16.0` can start both applications

### 15. MongoDB and Redis are not locally installed on `PATH`

Impact:

* local persistence-dependent tests need Docker or manual service setup

### 16. Docker Desktop CLI is installed but the Linux engine is stopped

Impact:

* Docker-based local flows require an explicit startup step

Evidence:

* `docker --version` and `docker compose version` succeed
* `docker info` cannot connect to the Docker Desktop Linux engine pipe

## Automation implications

1. Start with smoke and contract tests.
2. Treat many feature tests as blocked until the SUT changes.
3. Make Mongo and Redis validation optional.
4. Keep failure messaging precise so the framework reports SUT defects cleanly.
