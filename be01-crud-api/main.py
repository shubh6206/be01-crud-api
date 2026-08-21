import sqlite3
import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, Request, Response, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Database configuration
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")

class Database:
    """Manages SQLite database connections with cross-filesystem compatibility."""
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = os.path.abspath(db_file)
        self.is_direct = self._check_direct_access()
        if self.is_direct:
            self.active_path = self.db_file
        else:
            self.active_path = f"/tmp/tasks_active_{os.getpid()}.db"
            if os.path.exists(self.db_file) and os.path.getsize(self.db_file) > 0:
                try:
                    shutil.copyfile(self.db_file, self.active_path)
                except Exception:
                    pass
            elif os.path.exists(self.active_path):
                try:
                    os.remove(self.active_path)
                except Exception:
                    pass

        self.conn = sqlite3.connect(self.active_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def _check_direct_access(self) -> bool:
        test_file = f"{self.db_file}.test_lock"
        try:
            c = sqlite3.connect(test_file)
            c.execute("CREATE TABLE _t (id INT)")
            c.execute("DROP TABLE _t")
            c.close()
            if os.path.exists(test_file):
                os.remove(test_file)
            return True
        except Exception:
            if os.path.exists(test_file):
                try: os.remove(test_file)
                except: pass
            return False

    def execute(self, sql: str, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur

    def executemany(self, sql: str, seq_of_params):
        cur = self.conn.cursor()
        cur.executemany(sql, seq_of_params)
        return cur

    def commit(self):
        self.conn.commit()
        if not self.is_direct:
            try:
                with open(self.active_path, "rb") as src, open(self.db_file, "wb") as dst:
                    dst.write(src.read())
            except (PermissionError, OSError):
                pass

    def close(self):
        self.commit()
        self.conn.close()

# Global database instance
db = Database()

def init_db():
    """Initializes the database schema, indexes, and seeds initial tasks if empty."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Performance indexes for search and status filtering
    db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title)")
    db.commit()

    # Seed three example tasks inside a transaction only if table is empty
    count = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        db.execute("BEGIN TRANSACTION")
        db.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Buy groceries", 0),
                ("Read FastAPI documentation", 0),
                ("Complete Stage 2 assignment", 1)
            ]
        )
        db.commit()

# Run database initialization
init_db()

# App metadata for Swagger UI
app = FastAPI(
    title="Task API (SQLite Database)",
    description="A persistent RESTful CRUD API for managing a To-Do list backed by SQLite.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Schemas
class Task(BaseModel):
    id: int = Field(..., description="Unique task identifier", example=1)
    title: str = Field(..., description="Task title/description", example="Buy groceries")
    done: bool = Field(False, description="Completion status", example=False)

class TaskCreate(BaseModel):
    title: str = Field(..., description="Title of the new task", example="Buy milk")

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated task title", example="Buy organic milk")
    done: Optional[bool] = Field(None, description="Updated completion status", example=True)

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message description", example="Task not found")

class APIInfo(BaseModel):
    name: str = "Task API"
    version: str = "2.0"
    storage: str = "SQLite (tasks.db)"
    endpoints: List[str] = ["/tasks"]

class HealthResponse(BaseModel):
    status: str = "ok"

class TaskStats(BaseModel):
    total: int = Field(..., example=3)
    done: int = Field(..., example=1)
    open: int = Field(..., example=2)

@app.get(
    "/",
    response_model=APIInfo,
    tags=["General"],
    summary="Get API Root Information",
    description="Returns metadata about the Task API, version, storage layer, and available core endpoints."
)
def read_root():
    return {
        "name": "Task API",
        "version": "2.0",
        "storage": "SQLite (tasks.db)",
        "endpoints": ["/tasks"]
    }

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["General"],
    summary="Health Check Endpoint",
    description="Returns health status of the FastAPI service."
)
def read_health():
    return {"status": "ok"}

@app.get(
    "/tasks",
    response_model=List[Task],
    tags=["Tasks"],
    summary="List All Tasks",
    description="Retrieves tasks from SQLite database. Supports filtering by status (`?done=`), keyword search (`?search=`), and sorting (`?sort=title`)."
)
def get_tasks(
    done: Optional[bool] = Query(None, description="Filter tasks by completion status (true or false)"),
    search: Optional[str] = Query(None, description="Filter tasks whose title contains the search keyword (case-insensitive)"),
    sort: Optional[str] = Query(None, description="Sort tasks alphabetically ('title') or chronologically ('id')")
):
    query = "SELECT id, title, done FROM tasks"
    conditions = []
    params = []

    if done is not None:
        conditions.append("done = ?")
        params.append(1 if done else 0)

    if search is not None and search.strip():
        conditions.append("title LIKE ?")
        params.append(f"%{search.strip()}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    if sort == "title":
        query += " ORDER BY title COLLATE NOCASE ASC"
    else:
        query += " ORDER BY id ASC"

    cursor = db.execute(query, params)
    rows = cursor.fetchall()
    return [
        {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
        for row in rows
    ]

@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    responses={404: {"model": ErrorResponse, "description": "Task not found"}},
    tags=["Tasks"],
    summary="Get Task by ID",
    description="Retrieves a single task from SQLite by its ID. Returns 404 if not found."
)
def get_task(task_id: int):
    cursor = db.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if not row:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"}
        )
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse, "description": "Validation Error / Bad Request"}},
    tags=["Tasks"],
    summary="Create a New Task",
    description="Creates a new task in SQLite with auto-incremented ID and default done=False."
)
async def create_task(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid JSON payload"}
        )

    if not isinstance(data, dict):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Request body must be a JSON object"}
        )

    title = data.get("title")
    if title is None or not isinstance(title, str) or not title.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title is required and cannot be empty"}
        )

    clean_title = title.strip()
    cursor = db.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (clean_title, 0))
    db.commit()
    new_id = cursor.lastrowid

    new_task = {
        "id": new_id,
        "title": clean_title,
        "done": False
    }
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=new_task)

@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    responses={
        400: {"model": ErrorResponse, "description": "Validation Error / Bad Request"},
        404: {"model": ErrorResponse, "description": "Task not found"}
    },
    tags=["Tasks"],
    summary="Update an Existing Task",
    description="Updates the title and/or completion status of an existing task in SQLite."
)
async def update_task(task_id: int, request: Request):
    cursor = db.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    existing_task = cursor.fetchone()
    if not existing_task:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"}
        )

    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid JSON payload"}
        )

    if not isinstance(data, dict) or not data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Request body must be a non-empty JSON object"}
        )

    new_title = existing_task["title"]
    new_done = existing_task["done"]
    has_update = False

    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or not title.strip():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Title cannot be empty"}
            )
        new_title = title.strip()
        has_update = True

    if "done" in data:
        done = data["done"]
        if not isinstance(done, bool):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Done field must be a boolean"}
            )
        new_done = 1 if done else 0
        has_update = True

    if not has_update:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "No valid fields provided for update"}
        )

    db.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, new_done, task_id)
    )
    db.commit()

    return {
        "id": task_id,
        "title": new_title,
        "done": bool(new_done)
    }

@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse, "description": "Task not found"}},
    tags=["Tasks"],
    summary="Delete a Task",
    description="Removes a task from SQLite by its ID. Returns status 204 No Content upon success."
)
def delete_task(task_id: int):
    cursor = db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if not row:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"}
        )

    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get(
    "/stats",
    response_model=TaskStats,
    tags=["Extras"],
    summary="Get Task Statistics via SQL",
    description="Computes summary counts (total, done, open) directly via SQL COUNT queries."
)
def get_stats():
    total = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    done_count = db.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
    open_count = total - done_count
    return {
        "total": total,
        "done": done_count,
        "open": open_count
    }

@app.post(
    "/reset",
    tags=["Extras"],
    summary="Reset Task Database to Seed State",
    description="Resets the SQLite tasks table to the default 3 seed tasks using an atomic transaction."
)
def reset_tasks():
    db.execute("BEGIN TRANSACTION")
    db.execute("DELETE FROM tasks")
    db.execute("DELETE FROM sqlite_sequence WHERE name='tasks'")
    db.executemany(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        [
            ("Buy groceries", 0),
            ("Read FastAPI documentation", 0),
            ("Complete Stage 2 assignment", 1)
        ]
    )
    db.commit()

    rows = db.execute("SELECT id, title, done FROM tasks ORDER BY id ASC").fetchall()
    tasks_list = [
        {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
        for row in rows
    ]
    return {
        "message": "Task database successfully reset to default seed state",
        "tasks": tasks_list
    }
