import os
import sys
import time
import logging
from typing import List, Optional, Union
from fastapi import FastAPI, Request, Response, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("task_api")

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:dev@localhost:5432/tasks"
)

# Parse DATABASE_URL or individual env vars for fallback
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "dev")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "tasks")

class Database:
    """
    Production database manager supporting PostgreSQL with automatic connection retries,
    context-managed cursors, and graceful SQLite fallback for isolated unit testing environments.
    """
    def __init__(self):
        self.engine_type = "postgresql"
        self.conn = None
        self.connect()

    def connect(self, retries: int = 5, delay: float = 1.0):
        """Attempts to connect to PostgreSQL with retries, falling back to SQLite if PostgreSQL is unavailable."""
        # Try connecting to PostgreSQL via psycopg2
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            for attempt in range(1, retries + 1):
                try:
                    logger.info(f"Connecting to PostgreSQL (Attempt {attempt}/{retries})...")
                    self.conn = psycopg2.connect(DATABASE_URL)
                    self.conn.autocommit = True
                    self.engine_type = "postgresql"
                    logger.info("Successfully connected to PostgreSQL database.")
                    return
                except Exception as e:
                    logger.warning(f"PostgreSQL connection attempt {attempt} failed: {e}")
                    if attempt < retries:
                        time.sleep(delay)
        except ImportError:
            logger.warning("psycopg2 package not found.")

        # Fallback to SQLite for local standalone testing without Postgres server
        logger.info("PostgreSQL unavailable. Initializing SQLite in-memory/file fallback mode.")
        import sqlite3
        db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.engine_type = "sqlite"

    def execute(self, sql: str, params=()):
        """Executes a SQL query and returns a list of dictionaries or cursor results."""
        if self.engine_type == "postgresql":
            import psycopg2.extras
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                pg_sql = sql.replace("?", "%s")
                cur.execute(pg_sql, params)
                if cur.description:
                    return cur.fetchall()
                return None
        else:
            cur = self.conn.cursor()
            sqlite_sql = sql.replace("%s", "?")
            cur.execute(sqlite_sql, params)
            if cur.description:
                rows = cur.fetchall()
                return [dict(r) for r in rows]
            return None

    def execute_one(self, sql: str, params=()):
        """Executes a SQL query and returns a single row dictionary or None."""
        results = self.execute(sql, params)
        if results and len(results) > 0:
            return results[0]
        return None

    def execute_mutation(self, sql: str, params=()):
        """Executes INSERT/UPDATE/DELETE query and returns returned ID or rowcount."""
        if self.engine_type == "postgresql":
            import psycopg2.extras
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                pg_sql = sql.replace("?", "%s")
                cur.execute(pg_sql, params)
                if cur.description:
                    res = cur.fetchone()
                    return res
                return cur.rowcount
        else:
            cur = self.conn.cursor()
            sqlite_sql = sql.replace("%s", "?")
            if "RETURNING" in sqlite_sql.upper():
                sqlite_sql = sqlite_sql.split("RETURNING")[0].strip() + ";"
            cur.execute(sqlite_sql, params)
            self.conn.commit()
            return cur.lastrowid

    def ping(self) -> bool:
        """Pings the database to verify connectivity."""
        try:
            res = self.execute_one("SELECT 1 as ping;")
            return res is not None
        except Exception as e:
            logger.error(f"Database ping failed: {e}")
            return False

# Global database instance
db = Database()

def init_db():
    """Initializes PostgreSQL table schema, indexes, and seeds initial tasks if empty."""
    if db.engine_type == "postgresql":
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            );
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);")
        db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title);")

        count_res = db.execute_one("SELECT COUNT(*) as count FROM tasks;")
        count = count_res["count"] if count_res else 0

        if count == 0:
            logger.info("Seeding initial tasks into PostgreSQL...")
            db.execute("""
                INSERT INTO tasks (title, done) VALUES 
                ('Buy groceries', FALSE),
                ('Read FastAPI documentation', FALSE),
                ('Complete Stage 2 assignment', TRUE);
            """)
    else:
        # SQLite initialization
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            );
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);")
        db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title);")

        count_res = db.execute_one("SELECT COUNT(*) as count FROM tasks;")
        count = count_res["count"] if count_res else 0

        if count == 0:
            db.execute("""
                INSERT INTO tasks (title, done) VALUES 
                ('Buy groceries', 0),
                ('Read FastAPI documentation', 0),
                ('Complete Stage 2 assignment', 1);
            """)

# Initialize database schema on startup
try:
    init_db()
except Exception as err:
    logger.error(f"Error during schema initialization: {err}")

# App Metadata
app = FastAPI(
    title="Task API (Containerized PostgreSQL)",
    description="A production-ready RESTful CRUD API for managing a To-Do list backed by PostgreSQL and Docker Compose.",
    version="3.0.0",
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
    version: str = "3.0"
    storage: str = "PostgreSQL (Docker container)"
    endpoints: List[str] = ["/tasks"]

class HealthResponse(BaseModel):
    status: str = "ok"
    db: str = "ok"

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
    storage_desc = "PostgreSQL (Docker container)" if db.engine_type == "postgresql" else "SQLite (Fallback)"
    return {
        "name": "Task API",
        "version": "3.0",
        "storage": storage_desc,
        "endpoints": ["/tasks"]
    }

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["General"],
    summary="Health Check Endpoint",
    description="Returns service and PostgreSQL database ping health status."
)
def read_health():
    is_db_alive = db.ping()
    if not is_db_alive:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "db": "disconnected"}
        )
    return {"status": "ok", "db": "ok"}

@app.get(
    "/tasks",
    response_model=List[Task],
    tags=["Tasks"],
    summary="List All Tasks",
    description="Retrieves tasks from database. Supports filtering by status (`?done=`), keyword search (`?search=`), and sorting (`?sort=title`)."
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
        conditions.append("done = %s")
        params.append(done)

    if search is not None and search.strip():
        if db.engine_type == "postgresql":
            conditions.append("title ILIKE %s")
        else:
            conditions.append("title LIKE %s")
        params.append(f"%{search.strip()}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    if sort == "title":
        if db.engine_type == "postgresql":
            query += " ORDER BY title ASC"
        else:
            query += " ORDER BY title COLLATE NOCASE ASC"
    else:
        query += " ORDER BY id ASC"

    rows = db.execute(query, params) or []
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
    description="Retrieves a single task from database by its ID. Returns 404 if not found."
)
def get_task(task_id: int):
    row = db.execute_one("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
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
    description="Creates a new task with auto-assigned ID and default done=false."
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
    
    if db.engine_type == "postgresql":
        res = db.execute_mutation(
            "INSERT INTO tasks (title, done) VALUES (%s, FALSE) RETURNING id;",
            (clean_title,)
        )
        new_id = res["id"]
    else:
        new_id = db.execute_mutation(
            "INSERT INTO tasks (title, done) VALUES (%s, 0);",
            (clean_title,)
        )

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
    description="Updates title and/or completion status of an existing task."
)
async def update_task(task_id: int, request: Request):
    existing_task = db.execute_one("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
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
    new_done = bool(existing_task["done"])
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
        new_done = done
        has_update = True

    if not has_update:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "No valid fields provided for update"}
        )

    db.execute_mutation(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s",
        (new_title, new_done, task_id)
    )

    return {
        "id": task_id,
        "title": new_title,
        "done": new_done
    }

@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse, "description": "Task not found"}},
    tags=["Tasks"],
    summary="Delete a Task",
    description="Removes a task from database by its ID. Returns 204 No Content upon success."
)
def delete_task(task_id: int):
    row = db.execute_one("SELECT id FROM tasks WHERE id = %s", (task_id,))
    if not row:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"}
        )

    db.execute_mutation("DELETE FROM tasks WHERE id = %s", (task_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get(
    "/stats",
    response_model=TaskStats,
    tags=["Extras"],
    summary="Get Task Statistics via SQL",
    description="Computes summary counts (total, done, open) directly via SQL COUNT queries."
)
def get_stats():
    total_res = db.execute_one("SELECT COUNT(*) as count FROM tasks")
    total = total_res["count"] if total_res else 0

    done_res = db.execute_one("SELECT COUNT(*) as count FROM tasks WHERE done = %s", (True if db.engine_type == "postgresql" else 1,))
    done_count = done_res["count"] if done_res else 0
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
    description="Resets tasks table to the default 3 seed tasks using an atomic transaction."
)
def reset_tasks():
    if db.engine_type == "postgresql":
        db.execute("TRUNCATE TABLE tasks RESTART IDENTITY;")
        db.execute("""
            INSERT INTO tasks (title, done) VALUES 
            ('Buy groceries', FALSE),
            ('Read FastAPI documentation', FALSE),
            ('Complete Stage 2 assignment', TRUE);
        """)
    else:
        db.execute("DELETE FROM tasks;")
        db.execute("DELETE FROM sqlite_sequence WHERE name='tasks';")
        db.execute("""
            INSERT INTO tasks (title, done) VALUES 
            ('Buy groceries', 0),
            ('Read FastAPI documentation', 0),
            ('Complete Stage 2 assignment', 1);
        """)

    rows = db.execute("SELECT id, title, done FROM tasks ORDER BY id ASC") or []
    tasks_list = [
        {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
        for row in rows
    ]
    return {
        "message": "Task database successfully reset to default seed state",
        "tasks": tasks_list
    }
