# To-Do List CRUD API (W2 · A1 — BE-01)

A lightweight, robust RESTful CRUD API built with **Python 3.11** and **FastAPI** to manage a to-do list in memory. Built for the **Backend AI Engineering Track (Week 2 Assignment BE-01)**.

---

## 🚀 Quickstart: Install & Run

### Prerequisites
- Python 3.10 or higher
- `fastapi` and `uvicorn`

### Setup & One-Command Execution
```bash
# 1. Clone the repository
git clone https://github.com/shubham-smit/be01-crud-api.git
cd be01-crud-api

# 2. Run the server (Single Command)
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
The server will start at `http://localhost:8000`. Interactive Swagger UI documentation is available at `http://localhost:8000/docs`.

---

## 📌 API Endpoint Reference

| HTTP Method | Path | Description | Success Code | Error Codes |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | API Root Metadata | `200 OK` | — |
| **GET** | `/health` | Server Health Check | `200 OK` | — |
| **GET** | `/tasks` | List all tasks (supports `?done=` and `?search=`) | `200 OK` | — |
| **GET** | `/tasks/{id}` | Retrieve a single task by ID | `200 OK` | `404 Not Found` |
| **POST** | `/tasks` | Create a new task | `201 Created` | `400 Bad Request` |
| **PUT** | `/tasks/{id}` | Update task title and/or completion status | `200 OK` | `400 Bad Request`, `404 Not Found` |
| **DELETE** | `/tasks/{id}` | Remove a task from memory | `204 No Content` | `404 Not Found` |
| **GET** | `/stats` | Compute task count metrics | `200 OK` | — |
| **POST** | `/reset` | Reset task database to initial seed data | `200 OK` | — |

---

## 🧪 Verified `curl -i` Outputs

Below are raw terminal responses demonstrating the complete CRUD lifecycle and error handling:

### 1. Root & Health Endpoints
```http
$ curl -i http://localhost:8000/
HTTP/1.1 200 OK
date: Wed, 05 Aug 2026 14:50:21 GMT
server: uvicorn
content-length: 58
content-type: application/json

{"name":"Task API","version":"1.0","endpoints":["/tasks"]}

$ curl -i http://localhost:8000/health
HTTP/1.1 200 OK
date: Wed, 05 Aug 2026 14:50:21 GMT
server: uvicorn
content-length: 15
content-type: application/json

{"status":"ok"}
```

### 2. Read Endpoints (`GET /tasks` & `GET /tasks/{id}`)
```http
$ curl -i http://localhost:8000/tasks
HTTP/1.1 200 OK
date: Wed, 05 Aug 2026 14:50:33 GMT
server: uvicorn
content-length: 165
content-type: application/json

[{"id":1,"title":"Buy groceries","done":false},{"id":2,"title":"Read FastAPI documentation","done":false},{"id":3,"title":"Complete Stage 2 assignment","done":true}]

$ curl -i http://localhost:8000/tasks/1
HTTP/1.1 200 OK
date: Wed, 05 Aug 2026 14:50:33 GMT
server: uvicorn
content-length: 45
content-type: application/json

{"id":1,"title":"Buy groceries","done":false}

$ curl -i http://localhost:8000/tasks/99
HTTP/1.1 404 Not Found
date: Wed, 05 Aug 2026 14:50:33 GMT
server: uvicorn
content-length: 29
content-type: application/json

{"error":"Task 99 not found"}
```

### 3. Create Endpoint (`POST /tasks`)
```http
# Valid Creation
$ curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'
HTTP/1.1 201 Created
date: Wed, 05 Aug 2026 14:50:49 GMT
server: uvicorn
content-length: 40
content-type: application/json

{"id":4,"title":"Buy milk","done":false}

# Validation Error (Missing Title)
$ curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{}'
HTTP/1.1 400 Bad Request
date: Wed, 05 Aug 2026 14:50:49 GMT
server: uvicorn
content-length: 49
content-type: application/json

{"error":"Title is required and cannot be empty"}
```

### 4. Update Endpoint (`PUT /tasks/{id}`)
```http
$ curl -i -X PUT http://localhost:8000/tasks/4 \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy organic milk", "done":true}'
HTTP/1.1 200 OK
date: Wed, 05 Aug 2026 14:51:06 GMT
server: uvicorn
content-length: 47
content-type: application/json

{"id":4,"title":"Buy organic milk","done":true}
```

### 5. Delete Endpoint (`DELETE /tasks/{id}`)
```http
# Successful Deletion
$ curl -i -X DELETE http://localhost:8000/tasks/4
HTTP/1.1 204 No Content
date: Wed, 05 Aug 2026 14:51:06 GMT
server: uvicorn

# Subsequent Deletion Attempt
$ curl -i -X DELETE http://localhost:8000/tasks/4
HTTP/1.1 404 Not Found
date: Wed, 05 Aug 2026 14:51:06 GMT
server: uvicorn
content-length: 28
content-type: application/json

{"error":"Task 4 not found"}
```

---

## 📖 Swagger UI Interactive Documentation

FastAPI automatically generates interactive OpenAPI documentation at `/docs`.

```
========================================================================
                      TASK API — SWAGGER UI (/docs)
========================================================================
[General]
  GET  /        Get API Root Information
  GET  /health  Health Check Endpoint

[Tasks]
  GET    /tasks           List All Tasks (with query filters)
  POST   /tasks           Create a New Task (201 / 400)
  GET    /tasks/{task_id} Get Task by ID (200 / 404)
  PUT    /tasks/{task_id} Update an Existing Task (200 / 400 / 404)
  DELETE /tasks/{task_id} Delete a Task (204 / 404)

[Extras]
  GET  /stats   Get Task Statistics
  POST /reset   Reset Task List to Initial State
========================================================================
```

---

## 🧪 The Mortality Experiment

**Observation:** After creating new tasks via `POST /tasks`, stopping the uvicorn process (`CTRL+C`), and restarting the server, executing `GET /tasks` resets the list back to the initial 3 seed tasks.

**Why this happens:** Our task database is stored in a standard Python list residing purely in volatile RAM (Random Access Memory). When the server process terminates, the operating system releases the process memory address space. Upon restart, the script re-executes from top to bottom, re-initializing the `tasks` variable with default hardcoded objects. This highlights why persistent databases (e.g., PostgreSQL, SQLite) are required in production systems.

---

## 🎁 Extras & Stretch Features

1. **Filtering & Search:**
   - `GET /tasks?done=true` — returns completed tasks only.
   - `GET /tasks?search=read` — performs case-insensitive keyword search on titles.
2. **Statistics Endpoint:**
   - `GET /stats` — returns `{ "total": 3, "done": 1, "open": 2 }`.
3. **Reset Endpoint:**
   - `POST /reset` — resets the task list back to the default 3 seed items without restarting the server.

---

## 🤖 Stage 7 — AI Rematch ("AI vs Me")

### 1. Initial AI Prompt
> "Build a complete RESTful CRUD API in Python using FastAPI that manages a to-do list in memory. The API should serve GET /, GET /health, GET /tasks, GET /tasks/{id}, POST /tasks, PUT /tasks/{id}, and DELETE /tasks/{id}. Ensure POST assigns an incremented ID and default done=False. Validate input so missing titles return status 400 with a JSON error. Return 201 for create, 204 for delete, and 404 when task ID does not exist."

### 2. Execution & Checkpoint Test Results
- **Start Test:** Passed on the first attempt without syntax errors.
- **Checkpoint Results:**
  - `GET /`, `GET /health`, `GET /tasks`, `GET /tasks/1` -> **Passed** (200 OK)
  - `DELETE /tasks/1` -> **Passed** (204 No Content)
  - `POST /tasks` with `{}` -> **Failed** (Returned `422 Unprocessable Entity` instead of `400 Bad Request`)
  - `POST /tasks` with `{"title": "   "}` -> **Failed** (Accepted blank whitespace and returned `201 Created`)
  - Error key: **Failed** (Used `{"detail": "..."}` instead of `{"error": "..."}`)

### 3. Critical Analysis & Comparison
- **What the AI did better:** The AI cleanly structured Pydantic models (`TaskItem`, `TaskCreate`, `TaskUpdate`) and leveraged FastAPI's native type system for automatic documentation generation.
- **What it got wrong / quietly ignored:** The AI relied on default FastAPI/Pydantic request validation, which defaults to `422 Unprocessable Entity` for missing fields instead of the requested `400 Bad Request`. Furthermore, it did not strip whitespace strings, allowing empty titles to be saved.
- **What the prompt forgot to specify:** The prompt failed to specify the exact JSON error key (`error` vs `detail`) and did not explicitly instruct the AI to handle whitespace stripping and custom exception handlers.

### 4. Rematch Iteration & Resolution
- **Rematch Prompt:**
  > "Improve the FastAPI CRUD API. Add a custom exception handler for RequestValidationError to return status 400 Bad Request with JSON body `{'error': '...'}` instead of 422. Strip input titles and reject blank whitespace strings with status 400. Ensure all error responses use the key 'error'."
- **Result:** Version 2 (`ai-version/ai_app_v2.py`) passed 100% of validation and error checkpoints, matching our hand-built API specification.

---

## 📜 Commit History Log

```text
* 4a7311e Extras: filtering, search, stats, reset
* 0664cf5 Stage 5: Swagger UI
* b1770d3 Stage 4: full CRUD
* 9ac5565 Stage 3: create with validation
* c085b5c Stage 2: read endpoints with 404
* cc7ce90 Stage 1: root and health endpoints
* bc919cf Stage 0: hello server
```
