# SUT Analysis

Investigation date: July 25, 2026

## Scope

System under test:

* `social-app` - React + TypeScript + Vite frontend
* `social-network-advanced-backend` - Node.js + Express + Mongoose backend

Investigation goals:

1. Confirm startup/install commands and runtime requirements.
2. Derive actual frontend/backend behavior from source.
3. Run both applications where possible.
4. Record blockers that will shape the automation framework.

## Confirmed repository and runtime inventory

| Repository | Tech stack | Package manager | Install command | Start command | Confirmed status |
| --- | --- | --- | --- | --- | --- |
| `social-app` | React 18, TypeScript 5, Vite 5, MUI, MDB UI Kit, Axios, React Router | `npm` (`package-lock.json`) | `npm ci` (intended; not executed) | `npm run dev` | Existing `node_modules` were used. Vite dev server starts. `npm run build` fails on TypeScript errors. A clean install remains unverified. |
| `social-network-advanced-backend` | Express 4, Mongoose 8, bcryptjs, jsonwebtoken, dotenv, redis package installed | `npm` (`package-lock.json`) | `npm ci` (intended; not executed) | `node app.js` | Existing `node_modules` were used. `app.js` starts and serves `GET /` before exiting when MongoDB is unavailable. Route modules are not mounted, and some route modules fail to load. A clean install remains unverified. |
| `social-network-test-automation` | Empty repo at investigation time | N/A | N/A | N/A | New automation code must be created here only. |

## Confirmed Node.js requirements

Neither repository declares `engines` in its root `package.json`, but dependency metadata confirms the effective requirements:

| Repository | Evidence | Effective Node.js requirement |
| --- | --- | --- |
| `social-app` | `vite@5.4.0` requires `^18.0.0 || >=20.0.0` | Node 18+ or 20+ |
| `social-network-advanced-backend` | `mongoose@8.7.2` requires `>=16.20.1` | Node 16.20.1+ |

Recommended common version for both repos: Node 20 LTS.

Local machine observations:

* `node` and `npm` are on `PATH`.
* `node --version` reports `v24.18.0`.
* `npm --version` reports `11.16.0`.
* Node 24 is newer than the recommended common Node 20 LTS baseline. The
  investigation checks succeeded far enough to start Vite and Express, but the
  project should standardize on Node 20 LTS for reproducible local and CI runs.

## Environment variables

### Frontend

No frontend environment variables are implemented.

Confirmed configuration is hard-coded in source:

* `src/helpers/api.ts` sets Axios `baseURL` to `http://localhost:4002`
* `src/helpers/api.ts` sets `withCredentials: true`
* `src/helpers/default.ts` sets `BASE = 'http://localhost:4002'`

No `.env`, `.env.example`, `import.meta.env`, or Vite env usage was found.

### Backend

Confirmed backend environment variables used in source:

| Variable | Used in | Purpose |
| --- | --- | --- |
| `PORT` | `app.js` | Express listen port, default `5001`; read before dotenv initialization |
| `MONGO_URI` | `config/db.js` | MongoDB connection string |
| `JWT_SECRET` | `middleware/auth.js`, `utils/jwt.js` | JWT signing and verification |

Observations:

* `.gitignore` excludes `.env`.
* No `.env` or `.env.example` file exists in the repo.
* The backend cannot be started correctly in a clean environment without manually supplying at least `MONGO_URI` and `JWT_SECRET`.
* `app.js` evaluates `const PORT = process.env.PORT || 5001` before calling
  `dotenv.config()`. Therefore, `PORT` from the backend `.env` file is loaded too
  late and is ignored. A process-level `PORT` set before `node app.js` works.
  `MONGO_URI` is read later by the asynchronous database connection, and
  `JWT_SECRET` is read when tokens are signed or verified, so both can come from
  dotenv despite this ordering defect.

## Frontend architecture and behavior

## Routing

The real application entrypoint is `src/main.tsx`, not `src/App.tsx`.

`src/App.tsx` is still the default Vite sample component and is not used by the router.

Confirmed route map:

| Route | Component | Purpose |
| --- | --- | --- |
| `/` | `Signup` | Registration form |
| `/login` | `Login` | Login form |
| `/profile` | `Layout -> Profile` | Main authenticated area |
| `/profile/albums` | `Photos` | Posts/media screen |
| `/profile/settings` | `Settings` | Privacy/password settings |
| `/profile/search` | `Search` | User search |
| `/profile/:id` | `Account` | Other user profile |
| `/profile/requests` | `Requests` | Follow request approvals |
| `/profile/followers` | `Followers` | Followers list |
| `/profile/followings` | `Followings` | Following list |

## Frontend auth assumptions

Frontend auth flow assumes cookie/session-style behavior:

* `verifyUser()` calls `GET /verify`
* `handleLogout()` calls `POST /logout`
* Axios is configured with `withCredentials: true`
* No JWT token storage or `Authorization` header handling exists in frontend code

The profile layout blocks rendering until `verifyUser()` returns a `user`.

## Frontend API contract actually coded

The frontend expects the backend at `http://localhost:4002` and calls these routes:

| Frontend function | Method | Path | Expected behavior |
| --- | --- | --- | --- |
| `handleSignup` | POST | `/signup` | Create user |
| `handleLogin` | POST | `/login` | Authenticate user |
| `verifyUser` | GET | `/verify` | Return current user |
| `handleLogout` | POST | `/logout` | Logout current user |
| `handleUpload` | PATCH | `/profile/upload` | Upload profile picture |
| `handlePostUpload` | POST | `/posts` | Upload post media + text |
| `getAllPosts` | GET | `/posts` | Return feed/gallery posts |
| `deletePost` | DELETE | `/posts/:id` | Delete post |
| `handlePrivacy` | PATCH | `/account/set` | Toggle privacy |
| `handlePasswordChange` | PATCH | `/update/password` | Change password |
| `handleLoginChange` | PATCH | `/update/login` | Change login |
| `searchUsers` | GET | `/search/:text` | Search users |
| `getAccount` | GET | `/account/:id` | Return profile details |
| `handleFollow` | POST | `/account/follow/:id` | Follow user |
| `handleUnfollow` | POST | `/account/unfollow/:id` | Unfollow user |
| `handleCancelation` | DELETE | `/request/cancel/:id` | Cancel follow request |
| `getAllRequests` | GET | `/requests` | Get follow requests |
| `acceptRequest` | PATCH | `/requests/accept/:id` | Accept request |
| `declineRequest` | PATCH | `/requests/decline/:id` | Decline request |
| `getAllFollowers` | GET | `/followers` | Get followers |
| `getAllFollowings` | GET | `/following` | Get following |
| `handlePostReaction` | POST | `/posts/react/:id` | Toggle like |
| `getPost` | GET | `/posts/:id` | Get one post with comments/likes |
| `handleComment` | POST | `/posts/comment/:id` | Add comment |

## Frontend request/response models

Frontend TypeScript contracts are internally inconsistent with its own rendering code:

* `IUser` contains `name`, `surname`, `login`, `password`, optional `picture`, `cover`, `followers`, `following`, `isPrivate`.
* `IResponse.payload` is typed as `unknown`.
* `IPost` contains `id`, `title`, `picture`, `likes`, `isLiked`, `comments`.
* `IComment` is typed only as `{ text: string }`.
* `Preview.tsx` actually expects comments shaped like `{ id, user, content }`.

This mismatch is one of the reasons `npm run build` fails.

## Frontend feature notes by area

### Registration and login

* Signup form requires `name`, `surname`, `login`, `password`.
* Login form captures `login` and `password`.
* There is no frontend support for email-based login.

### Profile/dashboard

* Profile photo upload uses hidden file input triggered by clicking the image.
* Follower and following counts are fetched during render, not inside `useEffect`, so the component will re-request data on every render.

### Posts, comments, gallery

* Posts page uses multipart `FormData` with keys `photo` and `content`.
* Like action is bound to an image with `onClick`, not a semantic button.
* Post preview modal expects enriched likes and comments data that the backend does not provide.

### Privacy/settings

* Privacy toggle is represented as a clickable image, not an accessible control.
* Password change logs the user out after success.

### Search/follows/requests

* Search executes on every text change after trim.
* Account page expects `connection` flags: `followsMe`, `following`, `requested`.
* Requests page expects request records shaped like `{ id, user: {...} }`.

## Backend architecture and behavior

## Actual running entrypoint

`app.js` currently does only the following:

1. import dependencies and evaluate `PORT` from the existing process environment,
   falling back to `5001`
2. call `dotenv.config()`
3. create the Express app
4. register `bodyParser.json()` and `bodyParser.urlencoded()`
5. call `connectDB()` without awaiting it
6. expose `GET /` -> `Social Media API is running...`
7. call `app.listen(PORT)`

Important: no route files from `routes/` are mounted in `app.js`.

Because `connectDB()` is not awaited, Express can begin accepting requests before
the MongoDB connection succeeds. During the runtime probe, the root endpoint was
briefly reachable, after which the database error path called `process.exit(1)`.

As a result, the only confirmed reachable runtime endpoint is:

* `GET /` -> `200 OK`, body `Social Media API is running...`

Any intended `/api/...` route returns `404` from the running app.

## Backend route inventory from source

The backend contains route modules for intended features, but they are not wired into `app.js`.

| Route file | Declared endpoints | Current state |
| --- | --- | --- |
| `routes/user.js` | register, login, profile read/update/delete, logout | File loads, but service imports are broken strings, so handlers fail when invoked |
| `routes/posts.js` | create/list/read/update/delete/like posts | File does not load because `middleware/auth.js` is syntactically broken |
| `routes/comment.js` | create/list/update/delete comments | File does not load because `middleware/auth.js` is syntactically broken |
| `routes/follows.js` | follow/unfollow/followers/following | File loads, but routes do not use auth middleware and call services with wrong inputs |
| `routes/feed.js` | feed | Placeholder response only |
| `routes/blocked.js` | block/unblock/list blocked users | File loads, but routes do not use auth middleware and list route calls wrong service |
| `routes/search.js` | search users/posts | Placeholder responses only |
| `routes/notifications.js` | list/mark-read/delete notifications | Placeholder responses only |
| `routes/chatting.js` | create/list chats and messages | Placeholder responses only |
| `routes/media.js` | upload/delete media | Placeholder responses only |
| `routes/settings.js` | get/update settings, change password | Placeholder responses only; service dependency commented out |

## Confirmed backend auth and JWT handling

Backend auth behavior in source:

* JWTs are created with `jwt.sign({ userId }, process.env.JWT_SECRET, { expiresIn: '1h' })`
* Auth middleware reads the raw `Authorization` header value
* Auth middleware does not strip a `Bearer ` prefix
* On success it sets `req.user = decoded.userId`
* On failure it returns:
  * `401 { "message": "No token provided, authorization denied" }`
  * `401 { "message": "Invalid token" }`

Critical mismatch:

* frontend expects cookie-based auth + `withCredentials`
* backend expects raw JWT in `Authorization`
* backend has no cookie parser, no session middleware, and no CORS configuration

Cross-origin auth would fail even if routes were mounted because:

* frontend points to `localhost:4002`
* backend listens on `5001`
* backend does not enable CORS for credentialed browser requests

## Confirmed backend request/response behavior by domain

### User routes

Declared routes:

* `POST /api/users/register`
* `POST /api/users/login`
* `GET /api/users/profile/:userId`
* `PUT /api/users/profile/:userId`
* `DELETE /api/users/profile/:userId`
* `POST /api/users/logout`

Actual source defect:

`routes/user.js` does not `require('../services/user')`. It assigns string literals such as `const registerUser = '../services/user';`.

Confirmed via direct handler invocation:

* register returns `500 { "message": "registerUser is not a function" }`
* login returns `401 { "message": "loginUser is not a function" }`

### Posts

Declared routes:

* `POST /api/posts`
* `GET /api/posts`
* `GET /api/posts/:postId`
* `PUT /api/posts/:postId`
* `DELETE /api/posts/:postId`
* `POST /api/posts/:postId/like`

Service contract:

* create expects `{ content }`
* like toggles like by `userId`
* update/delete enforce author ownership by comparing `post.author.toString()` with `userId`

Defects:

* route module cannot load because `middleware/auth.js` is corrupted
* no multipart handling for media uploads
* response shape does not match frontend expectations
* `deletePost()` uses `post.remove()`, which is undefined in Mongoose 8

### Comments

Declared routes:

* `POST /api/comments/:postId/comments`
* `GET /api/comments/:postId/comments`
* `PUT /api/comments/:postId/comments/:commentId`
* `DELETE /api/comments/:postId/comments/:commentId`

Service contract:

* add expects `{ content }`
* update/delete enforce author ownership

Defects:

* route module cannot load because `middleware/auth.js` is corrupted
* `deleteComment()` uses `comment.remove()`, which is undefined in Mongoose 8
* route shape does not match frontend `/posts/comment/:id`

### Follows

Declared routes:

* `POST /api/users/:userId/follow`
* `DELETE /api/users/:userId/unfollow`
* `GET /api/users/:userId/followers`
* `GET /api/users/:userId/following`

Defects:

* routes do not use auth middleware but call services with `req.user`
* follow service only updates target user's `followers`
* `followings` are never updated
* unfollow/filter result is not assigned back, so unfollow does not remove anything
* followers/following read routes ignore `req.params.userId` and use `req.user`

### Blocking

Declared routes:

* `POST /api/users/:userId/block`
* `DELETE /api/users/:userId/unblock`
* `GET /api/users/:userId/blocked`

Defects:

* routes do not use auth middleware but call services with `req.user`
* unblock/filter result is not assigned back
* list route calls `blocksService.block(req.user)` instead of `blocksService.blocks(...)`

### Feed, search, chat, notifications, media, settings

All of these are currently placeholders:

* they return fixed success messages
* they do not persist data
* most have no service layer
* they are not mounted into the running app

## MongoDB models and collections

Confirmed Mongoose models and collection names:

| File | Model name | Collection name | Fields |
| --- | --- | --- | --- |
| `models/user.js` | `User` | `users` | `username`, `email`, `password`, `followers`, `followings`, `blocks` |
| `models/post.js` | `posts` | `posts` | `content`, `author`, `likes`, `createdAt` |
| `models/comment.js` | `Comment` | `comments` | `content`, `author`, `post`, `createdAt` |

Schema observations:

* `user.password` is hashed with bcrypt in a `pre('save')` hook.
* `user.matchPassword()` compares plain password to hashed password.
* `post.author` and `post.likes` reference `users`, but there is no `users` model name, only `User`.
* `comment.post` references `Post`, but the post model is named `posts`.
* These inconsistent ref names will break or weaken population behavior.

## Redis usage

Redis is not used by application code.

Confirmed findings:

* `redis` exists in backend dependencies
* no backend source file imports `redis`
* no Redis client is created
* no cache/session/pub-sub logic exists

Implication for automation:

* Redis validation should stay optional and disabled by default until the SUT actually uses Redis.

## Authorization and ownership rules found in code

Only a small subset of ownership logic exists:

* post update/delete require `post.author.toString() === userId`
* comment update/delete require `comment.author.toString() === userId`

There are no confirmed authorization rules for:

* profile access
* follows
* blocks
* privacy-restricted accounts
* notifications
* chat/message ownership
* media ownership
* settings ownership

## Validation rules found in code

### Frontend validation

* Signup:
  * `name` required
  * `surname` required
  * `login` required
  * `password` required
* Login:
  * no explicit required validators
* Password change:
  * `old` required
  * `newpwd` required
* Search:
  * empty/whitespace text skips request
* Comment composer:
  * empty/whitespace text is not submitted

### Backend validation

* User:
  * `username` required, unique
  * `email` required, unique
  * `password` required
* Post:
  * `content` required
  * `author` required
* Comment:
  * `content` required
  * `author` required
  * `post` required

Missing backend validation:

* no email format validation
* no password strength rules
* no username length rules
* no content length/file size checks
* no request body schema validation middleware

## File-upload behavior

Frontend behavior:

* profile upload sends multipart `FormData` with key `picture`
* post upload sends multipart `FormData` with keys `photo` and `content`

Backend behavior:

* only `body-parser` json/urlencoded middleware is registered
* no `multer`, `busboy`, `formidable`, cloud storage SDK, or static asset serving exists
* `routes/media.js` only returns placeholder JSON messages

Conclusion:

File upload is not implemented end to end.

## Docker and local environment requirements

Confirmed local requirements to run the current repos:

* Node.js 18+ or 20+ for frontend
* Node.js 16.20.1+ for backend
* MongoDB for meaningful backend operation
* optionally Docker Desktop if MongoDB is containerized locally

Environment observations on this machine:

* Docker Desktop is installed
* Docker CLI `29.6.1` and Docker Compose `v5.3.0` are installed
* Docker Desktop's Linux engine is stopped
* `mongod` is not on `PATH`
* `redis-server` is not on `PATH`
* `python` is not available on `PATH`; Python 3.12 must be installed before
  automation implementation

No Docker assets were found in either SUT repo:

* no `Dockerfile`
* no `docker-compose.yml`
* no compose overrides

## Testability problems

### Cross-repo contract problems

1. Frontend targets `http://localhost:4002`; backend listens on `5001`.
2. Frontend assumes cookie auth; backend assumes raw JWT header auth.
3. Frontend request paths do not match backend paths.
4. Frontend request payloads do not match backend payloads.
5. Frontend response expectations do not match backend response shapes.

### Backend structural problems

1. `app.js` does not mount any route modules.
2. `middleware/auth.js` is corrupted by appended route code and causes syntax failure.
3. `routes/user.js` imports service functions incorrectly.
4. delete services use `remove()`, which is undefined in Mongoose 8.
5. many route files are placeholders only.

### Frontend quality problems

1. `npm run build` fails due TypeScript type errors.
2. `Profile` page triggers follower/following requests during render.
3. Several interactive controls are non-semantic images instead of buttons/toggles.
4. `src/App.tsx` is dead scaffold code and can mislead new contributors.

## Missing files, broken imports, and incomplete functionality

Confirmed issues that can prevent the application from working:

* missing backend `.env.example`
* no backend start script
* no backend route mounting
* corrupted `middleware/auth.js`
* missing/incorrect backend service imports in `routes/user.js`
* no file upload middleware
* no CORS configuration
* no Redis implementation despite dependency
* no Docker assets
* unused scaffold `src/App.tsx`
* incomplete backend feature routes returning placeholders

## Runtime verification summary

Confirmed by execution:

* frontend Vite dev server starts successfully
* frontend `GET http://127.0.0.1:5173/` returns `200`
* frontend production build fails
* frontend lint fails with three errors and two warnings
* backend's configured `npm test` command fails intentionally with
  `Error: no test specified`
* backend syntax checking fails only for `middleware/auth.js`
* backend route-module loading succeeds for nine routers and fails for
  `routes/comment.js` and `routes/posts.js` because both import the corrupted
  auth middleware
* backend `app.js` starts successfully with temporary env vars
* backend `GET http://127.0.0.1:5001/` returns `200` with
  `Social Media API is running...`
* backend `POST /api/users/register` returns `404` because routers are not
  mounted
* backend then exits after MongoDB connection refusal at `127.0.0.1:27017`
* Docker engine connection fails because Docker Desktop is not running

No dependency installation was run during the continued investigation because
both repositories already contained `node_modules`. Existing dependencies were
used as found.

## Executed command ledger

Commands below are listed by meaningful command rather than reproducing the
PowerShell wrappers used for polling and process cleanup.

| Command | Repository | Result |
| --- | --- | --- |
| `node --version` | workspace | Passed: `v24.18.0` |
| `npm --version` | workspace | Passed: `11.16.0` |
| `python --version` | workspace | Failed: Python executable not available |
| `docker --version` | workspace | Passed: Docker CLI `29.6.1` |
| `docker compose version` | workspace | Passed: Compose `v5.3.0` |
| `mongod --version` | workspace | Failed: command not found |
| `redis-server --version` | workspace | Failed: command not found |
| `npm run dev -- --host 127.0.0.1 --port 5173` | `social-app` | Passed: Vite ready; HTTP probe returned `200`; process stopped after probe |
| `npm run build` | `social-app` | Failed: TypeScript compilation errors in gallery, preview, dashboard, account, request, follower, and following code |
| `npm run lint` | `social-app` | Failed: 3 errors and 2 warnings |
| `npm test` | backend | Failed: package script is the default `Error: no test specified` command |
| `node --check <each project .js file>` | backend | Failed for `middleware/auth.js`; all other project JavaScript files passed syntax checking |
| `node -e "require('./routes/<route>.js')"` for every router | backend | Nine loaded; `comment.js` and `posts.js` failed via corrupted auth middleware |
| `node app.js` with temporary `PORT`, `MONGO_URI`, and `JWT_SECRET` | backend | Partially passed: server listened and root probe succeeded; process exited on MongoDB connection refusal |
| `GET http://127.0.0.1:5001/` | running backend | Passed: `200` |
| `POST http://127.0.0.1:5001/api/users/register` | running backend | Returned `404`, confirming routers are not mounted |
| `docker info --format '{{.ServerVersion}}'` | workspace | Failed: Docker Desktop Linux engine pipe unavailable |

## Bottom line

The frontend and backend are not currently integrated as a functioning system. The automation framework should be designed to:

1. validate each layer independently where possible;
2. document known SUT defects explicitly;
3. use API-assisted setup only after the backend contract is stabilized;
4. keep Mongo/Redis validation optional;
5. treat several planned end-to-end flows as blocked until the SUT is repaired.
