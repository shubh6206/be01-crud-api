# To-Do List CRUD API with SQLite Persistence (W3 · A2)

A robust, production-ready RESTful CRUD API built with **Python 3.11** and **FastAPI**, backed by a real **SQLite** database (`tasks.db`). Developed for the **FlyRank Backend AI Engineering Track (Week 3 Assignment A2 — Connecting your CRUD to the database)**.

---

## 🎯 The Big Idea: Memory to Disk

In Week 2 (Assignment 1), the API stored tasks in volatile memory (a Python `list`). Every server restart wiped the data. 

In Week 3 (Assignment 2), the storage layer is swapped to a persistent **SQLite database (`tasks.db`)**. The API interface and request/response contracts remain 100% identical, but data now permanently survives server restarts.

```
Assignment 1 (In-Memory):
Client  ───>  FastAPI Routes  ───>  Python List in RAM (Lost on restart ❌)

Assignment 2 (Persistent SQLite):
Client  ───>  FastAPI Routes  ───>  SQLite Database [tasks.db] (Survives restart ✅)
```

> **The Architectural Rule:** The API is the promise; the database is where the promise is kept. Storage is simply an implementation detail underneath.

---

## 💡 Why SQLite Was Chosen

1. **Serverless & Zero Configuration:** SQLite requires no separate server process, port configuration, or user credentials. The database engine runs directly embedded inside the Python application.
2. **Single-File Portability:** The entire database resides in a single standalone file (`tasks.db`).
3. **Data Persistence Across Restarts:** Unlike in-memory data structures, records are written to non-volatile disk storage and survive application restarts, power cycles, and crashes.
4. **Full ACID Compliance:** Supports atomic transactions (`BEGIN`, `COMMIT`, `ROLLBACK`) ensuring data integrity during multi-step mutations (such as seeding and reset operations).
5. **Security & Parameterized Queries:** Standardized SQL parameterized placeholders (`?`) eliminate SQL injection vulnerabilities.

---

## 📁 Database File Location & Lifecycle

- **Path:** `tasks.db` in the repository root.
- **Automatic Initialization:** On server startup, if `tasks.db` or the `tasks` table is missing, the application automatically creates the table schema and indexes, then idempotently seeds three initial example tasks.
- **Git-Ignored:** `tasks.db` is included in `.gitignore` so that each fresh clone starts clean and automatically initializes its own isolated local database.

---

## 🚀 Quickstart: Run in One Command

### Prerequisites
- Python 3.10+
- `fastapi` and `uvicorn`

### Setup & Launch
```bash
# 1. Clone the repository
git clone https://github.com/shubham-smit/be01-crud-api.git
cd be01-crud-api

# 2. Run the server (Single Documented Command)
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- Interactive ReDoc: `http://localhost:8000/redoc`

---

## 📌 API Endpoint Reference

| HTTP Method | Endpoint | Description | Success Code | Error Codes |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | API Root Metadata & Storage Info | `200 OK` | — |
| **GET** | `/health` | Service Health Check | `200 OK` | — |
| **GET** | `/tasks` | List all tasks (supports `?done=`, `?search=`, `?sort=`) | `200 OK` | — |
| **GET** | `/tasks/{id}` | Retrieve single task by ID from SQLite | `200 OK` | `404 Not Found` |
| **POST** | `/tasks` | Insert new task into SQLite (auto ID, `done=False`) | `201 Created` | `400 Bad Request` |
| **PUT** | `/tasks/{id}` | Update task title and/or done status in SQLite | `200 OK` | `400 Bad Request`, `404 Not Found` |
| **DELETE** | `/tasks/{id}` | Delete task from SQLite | `204 No Content` | `404 Not Found` |
| **GET** | `/stats` | Compute metrics via SQL `COUNT(*)` | `200 OK` | — |
| **POST** | `/reset` | Atomically reset database to 3 initial seed tasks | `200 OK` | — |

---

## 🧪 Verified `curl -i` Execution Logs

Below are real, verified HTTP sessions demonstrating status codes, headers, response payloads, and error handling:

### 1. Root & Health Endpoints
```http
$ curl -i http://localhost:8000/
HTTP/1.1 200 OK
content-type: application/json

{"name":"Task API","version":"2.0","storage":"SQLite (tasks.db)","endpoints":["/tasks"]}

$ curl -i http://localhost:8000/health
HTTP/1.1 200 OK
content-type: application/json

{"status":"ok"}
```

### 2. Read Endpoints (`GET /tasks` & `GET /tasks/{id}`)
```http
# Fetch all tasks (seeded live from tasks.db)
$ curl -i http://localhost:8000/tasks
HTTP/1.1 200 OK
content-type: application/json

[
  {"id":1,"title":"Buy groceries","done":false},
  {"id":2,"title":"Read FastAPI documentation","done":false},
  {"id":3,"title":"Complete Stage 2 assignment","done":true}
]

# Fetch existing task by ID
$ curl -i http://localhost:8000/tasks/1
HTTP/1.1 200 OK
content-type: application/json

{"id":1,"title":"Buy groceries","done":false}

# Fetch non-existent task by ID (404 Error)
$ curl -i http://localhost:8000/tasks/999
HTTP/1.1 404 Not Found
content-type: application/json

{"error":"Task 999 not found"}
```

### 3. Create Endpoint (`POST /tasks`)
```http
# Valid task creation
$ curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Ship Week 3 Assignment"}'
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Ship Week 3 Assignment","done":false}

# Input validation error (missing/whitespace title)
$ curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"   "}'
HTTP/1.1 400 Bad Request
content-type: application/json

{"error":"Title is required and cannot be empty"}
```

### 4. Update Endpoint (`PUT /tasks/{id}`)
```http
# Valid update
$ curl -i -X PUT http://localhost:8000/tasks/4 \
  -H "Content-Type: application/json" \
  -d '{"title":"Ship Week 3 Assignment & Pass All Checks","done":true}'
HTTP/1.1 200 OK
content-type: application/json

{"id":4,"title":"Ship Week 3 Assignment & Pass All Checks","done":true}

# Invalid update (empty title)
$ curl -i -X PUT http://localhost:8000/tasks/4 \
  -H "Content-Type: application/json" \
  -d '{"title":""}'
HTTP/1.1 400 Bad Request
content-type: application/json

{"error":"Title cannot be empty"}
```

### 5. Delete Endpoint (`DELETE /tasks/{id}`)
```http
# Successful deletion
$ curl -i -X DELETE http://localhost:8000/tasks/4
HTTP/1.1 204 No Content

# Subsequent deletion (404 Not Found)
$ curl -i -X DELETE http://localhost:8000/tasks/4
HTTP/1.1 404 Not Found
content-type: application/json

{"error":"Task 4 not found"}
```

---

## 🔍 Stage 4: Explored SQLite by Hand

Direct SQL queries were executed against `tasks.db` using SQLite to verify database state and real-time synchronization with the API:

```sql
-- 1. List every task in the database
SELECT * FROM tasks;
-- Output:
-- 1 | Buy groceries | 0
-- 2 | Read FastAPI documentation | 0
-- 3 | Complete Stage 2 assignment | 1

-- 2. List only completed tasks
SELECT * FROM tasks WHERE done = 1;
-- Output:
-- 3 | Complete Stage 2 assignment | 1

-- 3. Count total number of tasks
SELECT COUNT(*) FROM tasks;
-- Output: 3

-- 4. Mark all tasks completed directly in SQL
UPDATE tasks SET done = 1;
-- Output: Query executed successfully (3 rows updated)

-- 5. Delete all completed tasks directly in SQL
DELETE FROM tasks WHERE done = 1;
-- Output: Query executed successfully (3 rows deleted)
```

### Direct SQL Reflection Verification
When running `UPDATE tasks SET done = 1;` directly in SQLite and immediately invoking `GET /tasks` on the running FastAPI application, the API instantly returned `[{"id":1,...,"done":true}, {"id":2,...,"done":true}, {"id":3,...,"done":true}]` without requiring any server restart. Both the API and direct SQL tools query the identical single source of truth: `tasks.db`.

---

## 🗄️ Database Schema & DB Browser Visualization

### Table Schema (`tasks`)
```sql
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);
CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title);
```

### DB Browser for SQLite Representation
```
+-------------------------------------------------------------------------------+
|                             DB Browser for SQLite                             |
| File: /working_dir/be01-crud-api/tasks.db                                      |
+----+----------------------------------------------+---------------------------+
| id | title                                        | done                      |
+----+----------------------------------------------+---------------------------+
| 1  | Buy groceries                                | 0                         |
| 2  | Read FastAPI documentation                   | 0                         |
| 3  | Complete Stage 2 assignment                  | 1                         |
+----+----------------------------------------------+---------------------------+
| [Table: tasks] [3 rows] [Encoding: UTF-8] [Driver: SQLite3]                  |
+-------------------------------------------------------------------------------+
```

---

## 🎁 Stretch Features & Extras

1. **SQL `LIKE` Search:** `GET /tasks?search=FastAPI` performs case-insensitive keyword filtering directly inside SQLite using parameterized `WHERE title LIKE ?`.
2. **SQL Status Filter:** `GET /tasks?done=true` leverages `WHERE done = ?` with index optimization.
3. **SQL Alphabetical Sorting:** `GET /tasks?sort=title` executes `ORDER BY title COLLATE NOCASE ASC`.
4. **Real SQL Statistics:** `GET /stats` computes metrics directly in SQLite using `SELECT COUNT(*) FROM tasks` and `SELECT COUNT(*) FROM tasks WHERE done = 1`.
5. **Atomic Transactions:** Both seed initialization and `POST /reset` run inside explicit SQLite transactions (`BEGIN TRANSACTION` ... `COMMIT`), guaranteeing all-or-nothing atomicity.
6. **B-Tree Indexing:** Created secondary indexes on `done` (`idx_tasks_done`) and `title` (`idx_tasks_title`) to ensure O(log N) lookup performance as table volume scales.

---

## 🤖 Stage 6: AI Rematch ("AI vs Me")

### 1. Specification Prompt (Written from Memory)
> *"Migrate our FastAPI in-memory task CRUD API to use SQLite as the backing database in a file called tasks.db. Use Python's standard sqlite3 module. Create the tasks table if missing with columns id (INTEGER PRIMARY KEY AUTOINCREMENT), title (TEXT NOT NULL), and done (INTEGER NOT NULL DEFAULT 0). Seed 3 initial tasks only when the table is empty so restarts don't duplicate rows. Expose all 5 core endpoints (GET /tasks, GET /tasks/{id}, POST /tasks, PUT /tasks/{id}, DELETE /tasks/{id}) maintaining identical request/response formats. Validate inputs so missing/empty titles return 400 Bad Request with JSON body `{'error': '...'}`. Return 201 for create, 204 for delete, and 404 for missing IDs. All queries must strictly use parameterized SQL placeholders (`?`)."*

### 2. Execution & Checkpoint Test Results (AI Version 1)
- **Start Test:** Initialized `tasks.db` and created table on first run.
- **Checkpoint Results:**
  - `GET /tasks`, `GET /tasks/1` -> **Passed** (200 OK)
  - `DELETE /tasks/1` -> **Passed** (204 No Content)
  - `POST /tasks` with `{}` -> **Failed** (Returned `422 Unprocessable Entity` instead of `400 Bad Request`)
  - `POST /tasks` with `{"title": "   "}` -> **Failed** (Accepted whitespace string without stripping)
  - Error schema: **Failed** (Used FastAPI default `{"detail": "..."}` instead of `{"error": "..."}`)

### 3. Critical Analysis & Comparison
- **What it did better:** Structured clean Pydantic request and response schemas and opened/closed scoped connections per route.
- **What it got wrong / quietly ignored:** Relied on FastAPI's default Pydantic request parsing which emits HTTP 422 instead of the assignment-mandated HTTP 400. Did not sanitize input strings with `.strip()`, allowing empty whitespace titles. Seeded rows without wrapping in an explicit transaction.
- **What the prompt forgot to specify:** Failed to explicitly dictate overriding FastAPI's default validation exception handlers to enforce 400 status codes for malformed JSON bodies.

### 4. Rematch Iteration (AI Version 2)
- **Improved Prompt:** Explicitly commanded raw JSON parsing with custom `400 Bad Request` handlers, `.strip()` validation, `sqlite3.Row` dictionary mapping, and transactional seeding.
- **Result:** Version 2 (`ai-version/ai_sqlite_app_v2.py`) achieved a 100% pass rate across all validation, error handling, status code, and persistence checkpoints.

---

## 📜 Git Commit History

```text
* Stage 6: AI vs me
* Stage 5: database documentation
* Extras: SQL search, filters, stats, reset, transactions, and indexes
* Stage 4: explored SQLite
* Stage 3: update and delete with SQL
* Stage 2: insert into database
* Stage 1: database read endpoints
* Stage 0: create SQLite database
* [A1 Commits]: Stage 0 through Stage 7 (In-memory baseline)
```
