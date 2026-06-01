from fastapi import FastAPI
from fastapi.responses import FileResponse
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

@app.get("/tasks/live")
def live_tasks():
    db = SessionLocal()
    tasks = db.query(Task).all()
    db.close()
    
    result = []
    now = datetime.utcnow()
    
    for task in tasks:
        days_left = (task.due_date - now).days
        hours_left = int((task.due_date - now).total_seconds() / 3600)
        
        if task.is_completed:
            status = "✅ Completed"
            time_left = "Done"
        elif days_left < 0:
            status = "🔴 OVERDUE"
            time_left = f"Overdue by {abs(days_left)} days"
        elif days_left == 0:
            status = "🔴 DUE TODAY"
            time_left = f"{hours_left} hours left"
        elif days_left == 1:
            status = "🟠 DUE TOMORROW"
            time_left = "1 day left"
        elif days_left <= 3:
            status = "🟡 URGENT"
            time_left = f"{days_left} days left"
        else:
            status = "🟢 ON TRACK"
            time_left = f"{days_left} days left"
        
        result.append({
            "id": task.id,
            "title": task.title,
            "client_name": task.client_name,
            "client_email": task.client_email,
            "due_date": task.due_date.strftime("%Y-%m-%d"),
            "time_left": time_left,
            "status": status,
            "is_completed": task.is_completed
        })
    
    return result

@app.get("/")
def dashboard():
    return FileResponse("dashboard.html")