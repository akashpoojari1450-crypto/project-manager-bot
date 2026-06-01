from fastapi import FastAPI
from models import SessionLocal, Task
from scheduler import start_scheduler
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()
scheduler = start_scheduler()

class TaskCreate(BaseModel):
    title: str
    client_name: str
    client_email: str
    due_date: datetime

@app.post("/tasks")
def create_task(task: TaskCreate):
    db = SessionLocal()
    new_task = Task(**task.dict())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    db.close()
    return {"message": "Task created", "task_id": new_task.id}

@app.put("/tasks/{task_id}/complete")
def complete_task(task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    task.is_completed = True
    db.commit()
    db.close()
    return {"message": "Task marked complete"}

@app.get("/tasks")
def list_tasks():
    db = SessionLocal()
    tasks = db.query(Task).all()
    db.close()
    return tasks