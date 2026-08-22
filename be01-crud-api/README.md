# Auth · Login & Protect API (W2 · A4 — Auth · Login & Protect)

A secure, production-ready RESTful API built with **Python 3.11**, **FastAPI**, and **Supabase Auth** as the Identity Provider. Developed for the **FlyRank Backend AI Engineering Track (Week 2 Assignment A4)**.

---

## 🎯 The Big Idea: The Auth Trust Triangle

Secure authentication is a trust triangle between three parties: the **client**, your **backend server**, and the **Identity Provider (Supabase)**. Credentials (email & password) are sent to Supabase — your server never stores passwords or performs custom hashing.

```
Step                     Who does it            What happens
1. Sign up / Log in      Client ──> Supabase    Client sends email + password to Supabase.
2. The token             Supabase ──> Client    Supabase verifies credentials and returns a signed JWT access_token.
3. The request           Client ──> Backend     Client calls your backend attaching Authorization: Bearer <token>.
4. Verification          Backend ──> Supabase   Your server asks Supabase "is this token real?" via get_user(token).
```

---

## 🚀 Quickstart: Run in One Command

### Prerequisites
- Python 3.10+
- Dependencies: `fastapi`, `uvicorn`, `supabase`, `python-dotenv`

### Setup & Launch

```bash
# 1. Clone the repository
git clone https://github.com/shubh6206/be01-crud-api.git
cd be01-crud-api

# 2. Copy environment template & start server
cp .env.example .env
python main.py
```

- **API Base URL:** `http://localhost:8000`
- **Interactive Swagger UI (with Padlock):** `http://localhost:8000/docs`
- **Interactive ReDoc:** `http://localhost:8000/redoc`

---

## 🔐 Environment Variables & Secrets Management

Secrets live strictly in the git-ignored `.env` file:

- `.env` — Contains real Supabase credentials (strictly git-ignored).
- `.env.example` — Committed template showing required variable keys with safe defaults:

```env
# Supabase Credentials
SUPABASE_URL=https://your-project-url.supabase.co
SUPABASE_KEY=your_anon_key_here

# Application Port
PORT=8000
```

---

## 📌 API Endpoint Reference

| HTTP Method | Endpoint | Description | Auth Required | Success Code | Error Codes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | API Information & Health Status | None | `200 OK` | — |
| **GET** | `/public/info` | Public open information | None | `200 OK` | — |
| **POST** | `/auth/signup` | Register new user account | None | `201 Created` | `400 Bad Request` |
| **POST** | `/auth/login` | Authenticate & return JWT access_token | None | `200 OK` | `400 Bad Request`, `401 Unauthorized` |
| **POST** | `/auth/logout` | End user session | `Bearer <token>` | `204 No Content` | `401 Unauthorized` |
| **GET** | `/protected/profile` | Read private profile data | `Bearer <token>` | `200 OK` | `401 Unauthorized` |
| **GET** | `/protected/dashboard` | Read protected dashboard statistics | `Bearer <token>` | `200 OK` | `401 Unauthorized` |

---

## 🧪 Verified `curl -i` Execution Logs

### 1. Public Info (`GET /public/info`)

```bash
$ curl -i http://localhost:8000/public/info
HTTP/1.1 200 OK
content-type: application/json

{"message":"Welcome stranger! This info is public."}
```

### 2. Sign Up (`POST /auth/signup`)

```bash
# Missing required fields
$ curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":" "}'
HTTP/1.1 400 Bad Request
content-type: application/json

{"error":"Email and password are required"}

# Successful Signup
$ curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
HTTP/1.1 201 Created
content-type: application/json

{"user":{"id":"usr_mock_123456","email":"test@example.com","aud":"authenticated"}}
```

### 3. Log In (`POST /auth/login`)

```bash
# Invalid Credentials
$ curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"wrongpassword"}'
HTTP/1.1 401 Unauthorized
content-type: application/json

{"error":"Invalid login credentials"}

# Successful Log In
$ curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
HTTP/1.1 200 OK
content-type: application/json

{
  "access_token": "mock_jwt_access_token_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  "refresh_token": "mock_refresh_token_xyz987654321",
  "token_type": "bearer",
  "user": {"id":"usr_mock_123456","email":"test@example.com"}
}
```

### 4. Protected Profile & Token Verification (`GET /protected/profile`)

```bash
# Missing Token (401 Unauthorized)
$ curl -i http://localhost:8000/protected/profile
HTTP/1.1 401 Unauthorized
content-type: application/json

{"error":"Access token required"}

# Invalid/Tampered Token (401 Unauthorized)
$ curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer invalid_tampered_token"
HTTP/1.1 401 Unauthorized
content-type: application/json

{"error":"Invalid or expired token"}

# Valid Bearer Token (200 OK)
$ curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer mock_jwt_access_token_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
HTTP/1.1 200 OK
content-type: application/json

{"id":"usr_mock_123456","email":"test@example.com","role":"authenticated"}
```

### 5. Log Out (`POST /auth/logout`)

```bash
$ curl -i -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer mock_jwt_access_token_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
HTTP/1.1 204 No Content
```

---

## 🔒 Swagger UI Authorization

FastAPI's built-in Swagger UI at `http://localhost:8000/docs` includes an **Authorize** padlock button configured via `HTTPBearer`.
1. Click **Authorize** at the top right of `/docs`.
2. Paste the `access_token` returned by `/auth/login`.
3. Call `/protected/profile`, `/protected/dashboard`, or `/auth/logout` directly from the browser!

---

## 🤖 Stage 7: AI Rematch ("AI vs Me")

### 1. Specification Prompt (Written from Memory)
> *"Build a secure authentication API in Python using FastAPI and Supabase Auth as the Identity Provider. Implement 5 endpoints: POST /auth/signup, POST /auth/login, POST /auth/logout, GET /protected/profile, and GET /public/info. Never store or hash passwords locally. Verify access tokens via Supabase get_user(token) using a reusable FastAPI dependency (HTTPBearer). Return HTTP 400 for missing fields, HTTP 401 for invalid credentials or bad tokens, and HTTP 204 for logout. Configure Swagger UI with Bearer auth security scheme."*

### 2. Execution & Quarantine Test Results (AI Version 1)
- **Quarantined Code Path:** `ai-version/ai_auth_app.py`
- **Checkpoint Results:**
  - `POST /auth/signup` and `POST /auth/login` -> **Passed**
  - `GET /public/info` -> **Passed**
  - `GET /protected/profile` with no header -> **Failed** (Raised standard HTTP 500 / unhandled exception instead of formatted 401 JSON)
  - `GET /protected/profile` with `Authorization: Bearer <token>` -> **Failed** (Did not catch `get_user` API exceptions, causing crashes on invalid tokens).

### 3. Critical Analysis & Comparison
- **How it handled token extraction:** Used raw `Header(None)` and manual `.replace("Bearer ", "")`, which crashed if the header format was slightly malformed.
- **Security flaws introduced:** Did not safely wrap `get_user` in a try/except block; an invalid token raised an unhandled exception leaking stack traces instead of cleanly returning HTTP 401 `{"error": "Invalid or expired token"}`.
- **What the prompt forgot to specify:** Failed to mandate explicit Pydantic/FastAPI exception handlers for uniform `{ "error": "..." }` response formatting.

### 4. Rematch Iteration (AI Version 2)
- **Improved Prompt:** Explicitly commanded reusable `HTTPBearer` security dependencies with try/except exception wrappers and uniform `{ "error": "..." }` JSON responses.
- **Result:** Version 2 passed all token verification and error handling checkpoints with 100% compliance.

---

## 📜 Git Commit History

* Stage 7: AI vs me
* Stage 6: publish to GitHub and write README
* Stage 5: Swagger UI documentation with bearer auth
* Stage 4: auth middleware and logout endpoint
* Stage 3: profile route token verification
* Stage 2: public route and unverified protected route
* Stage 1: signup and login routes working
* Stage 0: setup server and supabase client
