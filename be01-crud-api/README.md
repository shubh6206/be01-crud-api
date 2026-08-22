# Containerized To-Do CRUD API (W1 · A3 — Containerize Your Stack)

A production-ready RESTful CRUD API built with **Python 3.11**, **FastAPI**, and **PostgreSQL**, fully containerized with **Docker** and **Docker Compose**. Developed for the **FlyRank Backend AI Engineering Track (Week 1 Assignment A3)**.

---

## 🎯 The Big Idea: Memory → SQLite → Containerized PostgreSQL

This project completes the three-tier evolution of storage architectures while maintaining 100% endpoint stability:

1. **Assignment 1 (In-Memory):** Ephemeral state stored in Python RAM; lost upon process exit.
2. **Assignment 2 (SQLite):** File-based persistence in `tasks.db`; survives local process restarts.
3. **Assignment 3 (Containerized PostgreSQL):** Full-stack containerization with a dedicated PostgreSQL database server running in Docker, backed by a persistent named volume (`taskdata`) and managed via environment secrets (`.env`).

```
Assignment 1 (In-Memory):
Client ───> FastAPI Routes ───> Volatile List in RAM (Lost on restart ❌)

Assignment 2 (SQLite):
Client ───> FastAPI Routes ───> tasks.db on Disk (Single-file persistent ✅)

Assignment 3 (Containerized PostgreSQL):
Client ───> [Docker: api] ───> [Docker: db (Postgres)] ───> Named Volume (Production multi-container ✅)
```

> **The Architectural Principle:** Swapping the underlying database engine from memory to SQLite to PostgreSQL leaves the client-facing HTTP interface completely untouched. Storage is an implementation detail.

---

## 🚀 Quickstart: Run in One Command

### Prerequisites
- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) installed.

### Setup & Launch

```bash
# 1. Clone the repository
git clone https://github.com/shubh6206/be01-crud-api.git
cd be01-crud-api

# 2. Copy environment template & start the entire stack (Single Command)
cp .env.example .env && docker compose up --build
```

- **API Base URL:** `http://localhost:8000`
- **Interactive Swagger UI:** `http://localhost:8000/docs`
- **Interactive ReDoc:** `http://localhost:8000/redoc`

To shut down the stack while keeping data safe in the persistent volume:
```bash
docker compose down
```

---

## 🔐 Environment Variables & Secrets Management

In adherence to Twelve-Factor App methodology, sensitive credentials are never committed to version control:

- `.env` — Contains real environment secrets (strictly git-ignored).
- `.env.example` — Committed template showing required variable keys with safe defaults:

```env
# PostgreSQL Connection URL
DATABASE_URL=postgresql://postgres:dev@localhost:5432/tasks

# Database Credentials
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dev
POSTGRES_DB=tasks

# Application Port
PORT=8000
```

Inside the Docker Compose network, `DATABASE_URL` is automatically configured to point to the `db` container: `postgresql://postgres:dev@db:5432/tasks`.

---

## 📌 API Endpoint Reference

| HTTP Method | Endpoint | Description | Success Code | Error Codes |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | API Root Metadata & Storage Layer Info | `200 OK` | — |
| **GET** | `/health` | Service & PostgreSQL Database Health Check | `200 OK` | `503 Service Unavailable` |
| **GET** | `/tasks` | List all tasks (supports `?done=`, `?search=`, `?sort=`) | `200 OK` | — |
| **GET** | `/tasks/{id}` | Retrieve single task by ID from PostgreSQL | `200 OK` | `404 Not Found` |
| **POST** | `/tasks` | Insert task into Postgres with auto-assigned ID | `201 Created` | `400 Bad Request` |
| **PUT** | `/tasks/{id}` | Update title and/or done status in Postgres | `200 OK` | `400 Bad Request`, `404 Not Found` |
| **DELETE** | `/tasks/{id}` | Delete task from Postgres | `204 No Content` | `404 Not Found` |
| **GET** | `/stats` | Compute task metrics directly via SQL `COUNT(*)` | `200 OK` | — |
| **POST** | `/reset` | Atomically reset database to initial 3 seed tasks | `200 OK` | — |

---

## 🧪 Verified `curl -i` Execution Logs

Below are verified terminal responses demonstrating the complete lifecycle against PostgreSQL:

### 1. Root & Health (with DB Ping)

```bash
$ curl -i http://localhost:8000/
HTTP/1.1 200 OK
content-type: application/json

{"name":"Task API","version":"3.0","storage":"PostgreSQL (Docker container)","endpoints":["/tasks"]}

$ curl -i http://localhost:8000/health
HTTP/1.1 200 OK
content-type: application/json

{"status":"ok","db":"ok"}
```

### 2. Read Endpoints (`GET /tasks` & `GET /tasks/{id}`)

```bash
# Fetch all tasks (seeded live from PostgreSQL)
$ curl -i http://localhost:8000/tasks
HTTP/1.1 200 OK
content-type: application/json

[
  {"id":1,"title":"Buy groceries","done":false},
  {"id":2,"title":"Read FastAPI documentation","done":false},
  {"id":3,"title":"Complete Stage 2 assignment","done":true}
]

# Fetch task by ID
$ curl -i http://localhost:8000/tasks/1
HTTP/1.1 200 OK
content-type: application/json

{"id":1,"title":"Buy groceries","done":false}

# Non-existent task (404 Not Found)
$ curl -i http://localhost:8000/tasks/999
HTTP/1.1 404 Not Found
content-type: application/json

{"error":"Task 999 not found"}
```

### 3. Create Endpoint (`POST /tasks`)

```bash
# Valid creation
$ curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Deploy to production"}'
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Deploy to production","done":false}

# Missing/Empty title validation error
$ curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"   "}'
HTTP/1.1 400 Bad Request
content-type: application/json

{"error":"Title is required and cannot be empty"}
```

### 4. Update Endpoint (`PUT /tasks/{id}`)

```bash
$ curl -i -X PUT http://localhost:8000/tasks/4 \
  -H "Content-Type: application/json" \
  -d '{"title":"Deploy to production & verify telemetry","done":true}'
HTTP/1.1 200 OK
content-type: application/json

{"id":4,"title":"Deploy to production & verify telemetry","done":true}
```

### 5. Delete Endpoint (`DELETE /tasks/{id}`)

```bash
# Successful deletion
$ curl -i -X DELETE http://localhost:8000/tasks/4
HTTP/1.1 204 No Content

# Subsequent delete attempt (404)
$ curl -i -X DELETE http://localhost:8000/tasks/4
HTTP/1.1 404 Not Found
content-type: application/json

{"error":"Task 4 not found"}
```

---

## 🗄️ Database Verification & Docker Inspection

### 1. Direct PostgreSQL Verification via `psql`

```bash
$ docker exec -it taskdb psql -U postgres -d tasks

tasks=# \dt
             List of relations
 Schema | Name  | Type  |  Owner   
--------+-------+-------+----------
 public | tasks | table | postgres
(1 row)

tasks=# SELECT * FROM tasks;
 id |             title              | done 
----+--------------------------------+------
  1 | Buy groceries                  | f
  2 | Read FastAPI documentation     | f
  3 | Complete Stage 2 assignment    | t
(3 rows)
```

### 2. Table Schema & Index Definitions

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);
CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title);
```

---

## 🎁 Stretch Features & Extras

1. **PostgreSQL Health Probe (`GET /health`):** Runs `SELECT 1;` against PostgreSQL and reports `{"status": "ok", "db": "ok"}`. Load balancers and container orchestrators use this endpoint for traffic routing.
2. **SQL ILIKE Search:** `GET /tasks?search=FastAPI` executes case-insensitive pattern matching directly in PostgreSQL using parameterized queries (`WHERE title ILIKE %s`).
3. **Status Filter & Sorting:** `GET /tasks?done=true` leverages B-tree index on `done`, and `GET /tasks?sort=title` sorts alphabetically at the database layer.
4. **Real SQL Statistics (`GET /stats`):** Computes total, completed, and open task counts in PostgreSQL using `SELECT COUNT(*) FROM tasks` and `SELECT COUNT(*) FROM tasks WHERE done = TRUE`.
5. **Multi-Stage Dockerfile:** Uses a 2-stage build (`builder` -> `runner`) to keep the production container lightweight and minimize vulnerability surface area.
6. **Container Healthchecks:** `compose.yaml` specifies a `pg_isready` healthcheck on the database container, ensuring the API container waits for PostgreSQL to be fully ready before accepting requests.

---

## 🤖 Stage 6: AI Rematch ("AI vs Me")

### 1. Specification Prompt (Written from Memory)
> *"Containerize our FastAPI task CRUD API using PostgreSQL as the backing database. Structure a Dockerfile and docker compose setup (compose.yaml) defining an api and a db service. Connect using DATABASE_URL loaded from .env (git-ignored, with .env.example provided). Create the tasks table on startup with id SERIAL PRIMARY KEY, title TEXT NOT NULL, and done BOOLEAN NOT NULL DEFAULT FALSE. Seed 3 initial tasks only if the table is empty. Support all 5 core endpoints (GET /tasks, GET /tasks/{id}, POST /tasks, PUT /tasks/{id}, DELETE /tasks/{id}) with parameterized queries (%s placeholders), custom 400 Bad Request handling for empty titles, and persistent data across restarts using a named Docker volume taskdata."*

### 2. Execution & Checkpoint Test Results (AI Version 1)
- **Startup:** Docker Compose started successfully.
- **Checkpoint Results:**
  - `GET /tasks`, `GET /tasks/1` -> **Passed** (200 OK)
  - `DELETE /tasks/1` -> **Passed** (204 No Content)
  - `POST /tasks` with `{}` -> **Failed** (Returned 422 Unprocessable Entity instead of 400 Bad Request)
  - `POST /tasks` with `{"title": "   "}` -> **Failed** (Did not strip whitespace, created blank task)
  - **Container coordination:** **Failed** (Omitted `condition: service_healthy` in `depends_on`, causing race conditions on cold start).

### 3. Critical Analysis & Comparison
- **What it did better:** Cleanly structured Pydantic schemas and utilized `psycopg` context managers (`with conn.cursor() as cur:`).
- **What it got wrong / quietly ignored:** Relied on FastAPI's default request body validation which generates HTTP 422 errors instead of HTTP 400. Did not sanitize input strings with `.strip()`. In `compose.yaml`, it used plain `depends_on: [db]` which only waits for the database container to start, not for PostgreSQL to finish socket initialization.
- **What the prompt forgot to specify:** Failed to explicitly mandate container healthcheck conditions in Docker Compose and custom exception handling for HTTP 400 status codes.

### 4. Rematch Iteration (AI Version 2)
- **Improved Prompt:** Explicitly commanded raw JSON parsing with `400 Bad Request` handlers, `.strip()` validation, and container healthcheck gating with `pg_isready`.
- **Result:** Version 2 (`ai-version/ai_postgres_app_v2.py`) passed all validation and container checkpoints with 100% compliance.

---

## 📜 Git Commit History

* Stage 6: AI vs me
* Stage 5: one-command stack + docs
* Extras: DB healthcheck, filtering, stats, reset, and indexes
* Stage 4: docker-compose the whole stack
* Stage 3: full CRUD on Postgres
* Stage 2: read from Postgres
* Stage 1: connect via .env and create table
* Stage 0: Postgres in Docker
* [A2 Commits]: Stage 0 through Stage 6 (SQLite persistence)
* [A1 Commits]: Stage 0 through Stage 7 (In-memory baseline)
