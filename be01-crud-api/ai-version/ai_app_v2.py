from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="Task API", version="1.0")

# Custom validation exception handler to return 400 instead of 422
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid input: missing or invalid title"}
    )

tasks_db = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read FastAPI documentation", "done": False},
    {"id": 3, "title": "Complete Stage 2 assignment", "done": True},
]

class TaskItem(BaseModel):
    id: int
    title: str
    done: bool

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def read_health():
    return {"status": "ok"}

@app.get("/tasks", response_model=List[TaskItem])
def get_tasks():
    return tasks_db

@app.get("/tasks/{id}", response_model=TaskItem)
def get_task(id: int):
    for task in tasks_db:
        if task["id"] == id:
            return task
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {id} not found"}
    )

@app.post("/tasks", response_model=TaskItem, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate):
    title = task_in.title.strip()
    if not title:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title is required and cannot be empty"}
        )
    new_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {"id": new_id, "title": title, "done": False}
    tasks_db.append(new_task)
    return new_task

@app.put("/tasks/{id}", response_model=TaskItem)
def update_task(id: int, task_in: TaskUpdate):
    for task in tasks_db:
        if task["id"] == id:
            if task_in.title is not None:
                title = task_in.title.strip()
                if not title:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"error": "Title cannot be empty"}
                    )
                task["title"] = title
            if task_in.done is not None:
                task["done"] = task_in.done
            return task
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {id} not found"}
    )

@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int):
    for i, task in enumerate(tasks_db):
        if task["id"] == id:
            tasks_db.pop(i)
            return None
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {id} not found"}
    )
