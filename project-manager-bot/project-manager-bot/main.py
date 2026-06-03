from fastapi import FastAPI, Cookie, Response, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from models import SessionLocal, Task, User
from scheduler import start_scheduler
from pydantic import BaseModel
from datetime import datetime
from risk_engine import analyze_risk
from auth import register_user, login_user, get_user_from_token
from pdf_report import generate_pdf, generate_completion_report
from fastapi.responses import StreamingResponse

app = FastAPI()
scheduler = start_scheduler()

class TaskCreate(BaseModel):
    title: str
    client_name: str
    client_email: str
    due_date: datetime

class AuthRequest(BaseModel):
    username: str
    password: str
    email: str = ""

@app.post("/register")
def register(data: AuthRequest):
    user = register_user(data.username, data.email, data.password)
    if not user:
        return JSONResponse({"error": "Username already exists"}, status_code=400)
    return {"message": "Account created! Please login."}

@app.post("/login")
def login(data: AuthRequest, response: Response):
    token = login_user(data.username, data.password)
    if not token:
        return JSONResponse({"error": "Invalid username or password"}, status_code=401)
    response.set_cookie("token", token, httponly=True)
    return {"message": "Login successful"}

@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "Logged out"}

@app.post("/tasks")
def create_task(task: TaskCreate, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    new_task = Task(**task.dict(), user_id=user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    db.close()
    return {"message": "Task created", "task_id": new_task.id}

@app.put("/tasks/{task_id}/complete")
def complete_task(task_id: int, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if task:
        task.is_completed = True
        db.commit()
        # Generate and email completion report
        try:
            task_data = {
                "title": task.title,
                "client_name": task.client_name,
                "client_email": task.client_email,
                "due_date_raw": task.due_date,
            }
            pdf_buffer = generate_completion_report(task_data, user.username, user.email)
            # Send email with PDF attachment
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            from dotenv import load_dotenv
            load_dotenv("/workspaces/project-manager-bot/project-manager-bot/project-manager-bot/.env")
            import os
            sender = os.getenv("EMAIL_USER")
            password = os.getenv("EMAIL_PASSWORD")
            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = user.email
            msg["Subject"] = f"✅ Task Completed: {task.title}"
            msg.attach(MIMEText(f"Hi {user.username},\n\nGreat work! The task '{task.title}' for client {task.client_name} has been marked as complete.\n\nPlease find the completion report attached.\n\nProject Manager Bot", "plain"))
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(pdf_buffer.read())
            encoders.encode_base64(attachment)
            attachment.add_header("Content-Disposition", f"attachment; filename=completed_{task.title[:20]}.pdf")
            msg.attach(attachment)
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, user.email, msg.as_string())
            server.quit()
            print(f"Completion report sent to {user.email}")
        except Exception as e:
            print(f"Completion report email failed: {e}")
    db.close()
    return {"message": "Task marked complete"}

@app.get("/tasks/live")
def live_tasks(token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    tasks = db.query(Task).filter(Task.user_id == user.id).all()
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
        risk = analyze_risk(task)
        result.append({
            "id": task.id,
            "title": task.title,
            "client_name": task.client_name,
            "client_email": task.client_email,
            "due_date": task.due_date.strftime("%Y-%m-%d"),
            "time_left": time_left,
            "status": status,
            "is_completed": task.is_completed,
            "risk_label": risk["label"],
            "risk_level": risk["level"]
        })
    return result

@app.get("/me")
def get_me(token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    return {"username": user.username, "email": user.email}

@app.get("/")
def dashboard():
    return FileResponse("dashboard.html")

@app.get("/login-page")
def login_page():
    return FileResponse("login.html")
