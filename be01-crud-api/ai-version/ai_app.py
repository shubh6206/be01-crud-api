from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Task API", version="1.0")

# In-memory storage created by AI
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
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

@app.post("/tasks", response_model=TaskItem, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate):
    # AI used Pydantic default validation (which returns 422 for {} instead of 400)
    # Also AI did not validate empty whitespace strings ("   ")
    new_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {"id": new_id, "title": task_in.title, "done": False}
    tasks_db.append(new_task)
    return new_task

@app.put("/tasks/{id}", response_model=TaskItem)
def update_task(id: int, task_in: TaskUpdate):
    for task in tasks_db:
        if task["id"] == id:
            if task_in.title is not None:
                task["title"] = task_in.title
            if task_in.done is not None:
                task["done"] = task_in.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int):
    for i, task in enumerate(tasks_db):
        if task["id"] == id:
            tasks_db.pop(i)
            return None
    raise HTTPException(status_code=404, detail=f"Task {id} not found")
