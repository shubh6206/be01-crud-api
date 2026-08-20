from typing import List, Optional
from fastapi import FastAPI, Request, Response, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import sqlite3

 # database creation
def init_db():
    conn=sqlite3.connect("tasks.db")
    cursor=conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done INTEGER DEFAULT 0
        )
        """)

    #check if the table isempty by counting the rows
    cursor.execute('Select count(*) from tasks')
    count=cursor.fetchone()[0]

    #Seed three example tasks only if the count is 0
    if count==0:
        seed_tasks=[
            ('set up SQLite database',1),
            ('Write raw SQL queries',0),
            ("Complete the Backend internship",0)
        ]
        #Using a parametrised query to insert multiple rowa safely
        cursor.executemany(
            "Insert Into tasks (title,done) VALUES (?,?)",
            seed_tasks
        )
        conn.commit()
        conn.close()

init_db()

# App metadata for Swagger UI
app = FastAPI(
    title="Task API",
    description="A lightweight in-memory RESTful CRUD API for managing a To-Do list built with FastAPI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Pydantic Schemas for Swagger UI Documentation
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
    version: str = "1.0"
    endpoints: List[str] = ["/tasks"]

class HealthResponse(BaseModel):
    status: str = "ok"

class TaskStats(BaseModel):
    total: int = Field(..., example=3)
    done: int = Field(..., example=1)
    open: int = Field(..., example=2)

# Pre-filled in-memory task database
DEFAULT_TASKS = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read FastAPI documentation", "done": False},
    {"id": 3, "title": "Complete Stage 2 assignment", "done": True},
]

tasks = [dict(t) for t in DEFAULT_TASKS]

@app.get(
    "/",
    response_model=APIInfo,
    tags=["General"],
    summary="Get API Root Information",
    description="Returns metadata about the Task API, including name, version, and available core endpoints."
)
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["General"],
    summary="Health Check Endpoint",
    description="Used by automated monitoring systems to verify that the server process is healthy and active."
)
def read_health():
    return {"status": "ok"}

@app.get(
    "/tasks",
    response_model=List[Task],
    tags=["Tasks"],
    summary="List All Tasks",
    description="Retrieves all tasks stored in memory. Supports optional filtering by completion status or search keyword."
)
def get_tasks(
    done: Optional[bool] = Query(None, description="Filter tasks by completion status (true or false)"),
    search: Optional[str] = Query(None, description="Filter tasks whose title contains the search keyword (case-insensitive)")
):
    result = tasks
    if done is not None:
        result = [t for t in result if t["done"] == done]
    if search is not None and search.strip():
        term = search.strip().lower()
        result = [t for t in result if term in t["title"].lower()]
    return result

@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    responses={404: {"model": ErrorResponse, "description": "Task not found"}},
    tags=["Tasks"],
    summary="Get Task by ID",
    description="Retrieves a single task by its unique ID parameter. Returns 404 if the task ID does not exist."
)
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {task_id} not found"}
    )

@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse, "description": "Validation Error / Bad Request"}},
    tags=["Tasks"],
    summary="Create a New Task",
    description="Creates a new task with an auto-assigned ID and default completion status of False. Requires a non-empty title."
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

    next_id = max([t["id"] for t in tasks], default=0) + 1
    new_task = {
        "id": next_id,
        "title": title.strip(),
        "done": False
    }
    tasks.append(new_task)
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
    description="Updates the title and/or completion status of an existing task identified by its ID."
)
async def update_task(task_id: int, request: Request):
    target_task = None
    for task in tasks:
        if task["id"] == task_id:
            target_task = task
            break

    if not target_task:
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

    has_update = False
    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or not title.strip():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Title cannot be empty"}
            )
        target_task["title"] = title.strip()
        has_update = True

    if "done" in data:
        done = data["done"]
        if not isinstance(done, bool):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Done field must be a boolean"}
            )
        target_task["done"] = done
        has_update = True

    if not has_update:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "No valid fields provided for update"}
        )

    return target_task

@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse, "description": "Task not found"}},
    tags=["Tasks"],
    summary="Delete a Task",
    description="Removes a task from memory by its ID. Returns status 204 No Content upon success."
)
def delete_task(task_id: int):
    global tasks
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {task_id} not found"}
    )

@app.get(
    "/stats",
    response_model=TaskStats,
    tags=["Extras"],
    summary="Get Task Statistics",
    description="Computes and returns summary metrics: total tasks count, completed tasks count, and open/pending tasks count."
)
def get_stats():
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    open_count = total - done_count
    return {
        "total": total,
        "done": done_count,
        "open": open_count
    }

@app.post(
    "/reset",
    tags=["Extras"],
    summary="Reset Task List to Initial State",
    description="Restores the task list to its initial 3 seed tasks. Useful for demos and testing."
)
def reset_tasks():
    global tasks
    tasks = [dict(t) for t in DEFAULT_TASKS]
    return {"message": "Task list successfully reset to default seed state", "tasks": tasks}
