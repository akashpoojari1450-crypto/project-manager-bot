from fastapi import FastAPI, Cookie, Response, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from models import SessionLocal, Task, User, Team, TeamMember
from scheduler import start_scheduler
from pydantic import BaseModel
from datetime import datetime
from risk_engine import analyze_risk
from auth import register_user, login_user, get_user_from_token
from ai_brain import generate_daily_briefing, suggest_reschedule, chat_with_tasks
from pdf_report import generate_pdf, generate_completion_report
from fastapi.responses import StreamingResponse

app = FastAPI()
scheduler = start_scheduler()
import os
if os.path.exists("icon-192.png"):
    @app.get("/icon-192.png")
    def icon192():
        from fastapi.responses import FileResponse
        return FileResponse("icon-192.png")
    @app.get("/icon-512.png")
    def icon512():
        from fastapi.responses import FileResponse
        return FileResponse("icon-512.png")
    @app.get("/manifest.json")
    def manifest():
        from fastapi.responses import FileResponse
        return FileResponse("manifest.json")
    @app.get("/sw.js")
    def sw():
        from fastapi.responses import FileResponse
        return FileResponse("sw.js")

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
    try:
        from notifier import send_email
        send_email(
            data.email,
            "Welcome to Project Manage AI",
            "Hi " + data.username + ",\n\nWelcome to Project Manage AI\n\nYour account has been created.\n\nLogin: https://project-manager-bot-production.up.railway.app\n\nTeam Code Raiders"
        )
    except Exception as e:
        print(f"Welcome email failed: {e}")
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

    # Send email notification on task creation
    print(f"DEBUG: Creating task notification for user={user.username} email={user.email}")
    try:
        from notifier import send_email, send_whatsapp
        from datetime import timedelta
        IST = timedelta(hours=5, minutes=30)
        due_ist = (new_task.due_date + IST).strftime("%d %b %Y %I:%M %p")

        email_body = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px">
        <div style="max-width:600px;margin:auto;background:white;border-radius:12px;padding:30px;box-shadow:0 2px 10px rgba(0,0,0,0.1)">
          <h2 style="color:#1e3c72">📋 New Task Created</h2>
          <p>Hi <strong>{user.username}</strong>, a new task has been added to your project manager.</p>
          <table style="width:100%;border-collapse:collapse;margin:20px 0">
            <tr style="background:#f8f9ff"><td style="padding:10px;font-weight:bold">Task</td><td style="padding:10px">{new_task.title}</td></tr>
            <tr><td style="padding:10px;font-weight:bold">Client</td><td style="padding:10px">{new_task.client_name}</td></tr>
            <tr style="background:#f8f9ff"><td style="padding:10px;font-weight:bold">Due Date</td><td style="padding:10px">{due_ist} IST</td></tr>
            <tr><td style="padding:10px;font-weight:bold">Status</td><td style="padding:10px"><span style="color:green;font-weight:bold">✅ Active</span></td></tr>
          </table>
          <p style="color:#666">Login to your dashboard to track this task:</p>
          <a href="https://project-manager-bot-production.up.railway.app" style="background:#1e3c72;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;display:inline-block">Open Dashboard</a>
          <p style="color:#aaa;font-size:12px;margin-top:20px">AI-Powered Project Manager Bot</p>
        </div></body></html>
        """

        # Email to user
        if user.email:
            send_email(user.email, f"📋 New Task: {new_task.title}", email_body)

        # Email to client
        if new_task.client_email:
            client_body = f"""
            <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px">
            <div style="max-width:600px;margin:auto;background:white;border-radius:12px;padding:30px">
              <h2 style="color:#1e3c72">👋 Project Update from {user.username}</h2>
              <p>Dear <strong>{new_task.client_name}</strong>,</p>
              <p>A new task has been created for your project.</p>
              <table style="width:100%;border-collapse:collapse;margin:20px 0">
                <tr style="background:#f8f9ff"><td style="padding:10px;font-weight:bold">Task</td><td style="padding:10px">{new_task.title}</td></tr>
                <tr><td style="padding:10px;font-weight:bold">Due Date</td><td style="padding:10px">{due_ist} IST</td></tr>
                <tr style="background:#f8f9ff"><td style="padding:10px;font-weight:bold">Manager</td><td style="padding:10px">{user.username}</td></tr>
              </table>
              <p style="color:#aaa;font-size:12px">Sent by AI-Powered Project Manager Bot</p>
            </div></body></html>
            """
            send_email(new_task.client_email, f"📬 New Task Started: {new_task.title}", client_body)

        # WhatsApp to user
        whatsapp_msg = f"📋 *New Task Created*\n\n*Task:* {new_task.title}\n*Client:* {new_task.client_name}\n*Due:* {due_ist} IST\n\nLogin: https://project-manager-bot-production.up.railway.app"
        user_phone = getattr(user, 'phone', None)
        if user_phone:
            send_whatsapp(user_phone, whatsapp_msg)

    except Exception as e:
        print(f"Notification error: {e}")

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

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if task:
        db.delete(task)
        db.commit()
    db.close()
    return {"message": "Task deleted"}

@app.get("/me")
def get_me(token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    return {"username": user.username, "email": user.email}


@app.get("/analytics")
def analytics_page(token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return RedirectResponse("/login-page")
    return FileResponse("analytics.html")

@app.get("/analytics/data")
def analytics_data(token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    tasks = db.query(Task).filter(Task.user_id == user.id).all()
    db.close()
    now = datetime.utcnow()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.is_completed)
    overdue = sum(1 for t in tasks if not t.is_completed and t.due_date < now)
    urgent = sum(1 for t in tasks if not t.is_completed and 0 <= (t.due_date - now).days <= 3)
    on_track = total - completed - overdue - urgent
    from risk_engine import analyze_risk
    high_risk = sum(1 for t in tasks if not t.is_completed and "HIGH" in analyze_risk(t)["label"])
    med_risk = sum(1 for t in tasks if not t.is_completed and "MEDIUM" in analyze_risk(t)["label"])
    low_risk = sum(1 for t in tasks if not t.is_completed and ("LOW" in analyze_risk(t)["label"] or "ON TRACK" in analyze_risk(t)["label"]))
    return {
        "total": total,
        "completed": completed,
        "overdue": overdue,
        "urgent": urgent,
        "on_track": on_track,
        "high_risk": high_risk,
        "med_risk": med_risk,
        "low_risk": low_risk,
        "completion_rate": round((completed / total * 100) if total else 0, 1)
    }







@app.post("/chat")
async def chat(request: Request, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    db = SessionLocal()
    tasks = db.query(Task).filter(Task.user_id == user.id).all()
    db.close()

    body = await request.json()
    user_message = body.get("message", "")
    history = body.get("history", [])

    from datetime import timedelta
    from risk_engine import analyze_risk
    import os
    from dotenv import load_dotenv
    load_dotenv()

    now = datetime.utcnow()
    IST = timedelta(hours=5, minutes=30)
    task_lines = []
    for t in tasks:
        days_left = (t.due_date - now).days
        if t.is_completed: status = "Completed"
        elif days_left < 0: status = f"Overdue by {abs(days_left)} days"
        elif days_left == 0: status = "Due Today"
        elif days_left <= 3: status = f"Urgent - {days_left} days left"
        else: status = f"On Track - {days_left} days left"
        risk = analyze_risk(t)
        task_lines.append(
            f"- [{status}] {t.title} | Client: {t.client_name} | "
            f"Due: {(t.due_date+IST).strftime('%d %b %Y')} | Risk: {risk['label']}"
        )

    tasks_text = "\n".join(task_lines) if task_lines else "No tasks yet."

    system_prompt = f"""You are a smart AI assistant for {user.username}, a project manager.

You have access to their live task data:
{tasks_text}

You can:
- Answer questions about their tasks, deadlines, risks
- Give project management advice
- Answer any general question like ChatGPT
- Help write emails, plans, summaries

Be helpful, friendly, and concise. Use emojis where appropriate."""

    messages = []
    for h in history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_prompt}] + messages,
        max_tokens=1024,
        temperature=0.7
    )

    reply = response.choices[0].message.content
    return {"reply": reply}


import secrets

@app.get("/portal/generate/{task_id}")
def generate_portal_link(task_id: int, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        db.close()
        return JSONResponse({"error": "Task not found"}, status_code=404)
    if not task.client_token:
        task.client_token = secrets.token_urlsafe(32)
        db.commit()
    token_val = task.client_token
    db.close()
    return {"portal_url": f"/portal/{token_val}"}

@app.get("/portal/{client_token}")
def client_portal(client_token: str):
    db = SessionLocal()
    task = db.query(Task).filter(Task.client_token == client_token).first()
    if not task:
        db.close()
        return HTMLResponse("<h2>Invalid or expired link.</h2>", status_code=404)
    db.close()
    return FileResponse("client_portal.html")

@app.get("/portal/{client_token}/data")
def client_portal_data(client_token: str):
    db = SessionLocal()
    task = db.query(Task).filter(Task.client_token == client_token).first()
    if not task:
        db.close()
        return JSONResponse({"error": "Not found"}, status_code=404)
    from risk_engine import analyze_risk
    from datetime import timedelta
    IST = timedelta(hours=5, minutes=30)
    now = __import__("datetime").datetime.utcnow()
    days_left = (task.due_date - now).days
    if task.is_completed: status = "Completed"
    elif days_left < 0: status = f"Overdue by {abs(days_left)} days"
    elif days_left == 0: status = "Due Today"
    elif days_left <= 3: status = f"Urgent - {days_left} days left"
    else: status = f"On Track - {days_left} days left"
    risk = analyze_risk(task)
    db.close()
    return {
        "title": task.title,
        "client_name": task.client_name,
        "due_date": (task.due_date + IST).strftime("%d %b %Y"),
        "status": status,
        "risk": risk["label"],
        "is_completed": task.is_completed,
        "days_left": days_left,
        "description": getattr(task, "description", "")
    }


# ── TEAM ROUTES ──────────────────────────────────────────

class TeamCreate(BaseModel):
    name: str

class InviteMember(BaseModel):
    username: str

class AssignTask(BaseModel):
    username: str

@app.post("/teams")
def create_team(data: TeamCreate, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    team = Team(name=data.name, owner_id=user.id)
    db.add(team)
    db.commit()
    db.refresh(team)
    # Add owner as member
    member = TeamMember(team_id=team.id, user_id=user.id, role="owner")
    db.add(member)
    db.commit()
    db.close()
    return {"message": "Team created!", "team_id": team.id}

@app.post("/teams/{team_id}/invite")
def invite_member(team_id: int, data: InviteMember, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == user.id).first()
    if not team:
        db.close()
        return JSONResponse({"error": "Team not found or not your team"}, status_code=404)
    invite_user = db.query(User).filter(User.username == data.username).first()
    if not invite_user:
        db.close()
        return JSONResponse({"error": "User not found"}, status_code=404)
    existing = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == invite_user.id).first()
    if existing:
        db.close()
        return JSONResponse({"error": "User already in team"}, status_code=400)
    member = TeamMember(team_id=team_id, user_id=invite_user.id, role="member")
    db.add(member)
    db.commit()
    db.close()
    return {"message": f"{data.username} added to team!"}

@app.get("/teams")
def get_teams(token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    memberships = db.query(TeamMember).filter(TeamMember.user_id == user.id).all()
    teams = []
    for m in memberships:
        team = db.query(Team).filter(Team.id == m.team_id).first()
        members = db.query(TeamMember).filter(TeamMember.team_id == team.id).all()
        teams.append({
            "id": team.id,
            "name": team.name,
            "role": m.role,
            "member_count": len(members)
        })
    db.close()
    return teams

@app.get("/teams/{team_id}/tasks")
def get_team_tasks(team_id: int, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    member = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user.id).first()
    if not member:
        db.close()
        return JSONResponse({"error": "Not a team member"}, status_code=403)
    tasks = db.query(Task).filter(Task.team_id == team_id).all()
    from datetime import timedelta
    IST_OFFSET = timedelta(hours=5, minutes=30)
    now = datetime.utcnow() + IST_OFFSET
    result = []
    for task in tasks:
        due_ist = task.due_date + IST_OFFSET
        days_left = (due_ist - now).days
        assignee = db.query(User).filter(User.id == task.assigned_to).first()
        result.append({
            "id": task.id,
            "title": task.title,
            "client_name": task.client_name,
            "due_date": task.due_date.strftime("%Y-%m-%d"),
            "days_left": days_left,
            "is_completed": task.is_completed,
            "assigned_to": assignee.username if assignee else "Unassigned"
        })
    db.close()
    return result

@app.post("/tasks/{task_id}/assign")
def assign_task(task_id: int, data: AssignTask, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        db.close()
        return JSONResponse({"error": "Task not found"}, status_code=404)
    assignee = db.query(User).filter(User.username == data.username).first()
    if not assignee:
        db.close()
        return JSONResponse({"error": "User not found"}, status_code=404)
    task.assigned_to = assignee.id
    db.commit()
    db.close()
    return {"message": f"Task assigned to {data.username}!"}

@app.get("/teams/{team_id}/members")
def get_team_members(team_id: int, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    result = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        result.append({"username": u.username, "email": u.email, "role": m.role})
    db.close()
    return result


@app.get("/briefing")
def daily_briefing(token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    tasks = db.query(Task).filter(Task.user_id == user.id).all()
    db.close()
    try:
        from ai_brain import generate_daily_briefing
        briefing = generate_daily_briefing(tasks, user.username)
        return {"briefing": briefing}
    except Exception as e:
        return {"briefing": f"Error: {str(e)}"}


# ── Team Chat ─────────────────────────────────────────────────────────────────
from models import ChatMessage
from datetime import timezone

class ConnectionManager:
    def __init__(self):
        self.active: dict = {}  # room -> list of (websocket, username)

    async def connect(self, websocket: WebSocket, room: str, username: str):
        await websocket.accept()
        if room not in self.active:
            self.active[room] = []
        self.active[room].append((websocket, username))

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.active:
            self.active[room] = [(ws, u) for ws, u in self.active[room] if ws != websocket]

    async def broadcast(self, room: str, message: dict):
        import json
        if room in self.active:
            dead = []
            for ws, u in self.active[room]:
                try:
                    await ws.send_text(json.dumps(message))
                except:
                    dead.append((ws, u))
            for d in dead:
                self.active[room].remove(d)

manager = ConnectionManager()

@app.websocket("/ws/chat/{room}")
async def websocket_chat(websocket: WebSocket, room: str):
    token = websocket.cookies.get("token")
    user = get_user_from_token(token)
    if not user:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, room, user.username)

    # Send last 30 messages on join
    db = SessionLocal()
    history = db.query(ChatMessage).filter(
        ChatMessage.room == room
    ).order_by(ChatMessage.timestamp.desc()).limit(30).all()
    db.close()

    import json
    from datetime import timedelta
    IST = timedelta(hours=5, minutes=30)
    for msg in reversed(history):
        await websocket.send_text(json.dumps({
            "type": "history",
            "username": msg.username,
            "message": msg.message,
            "timestamp": (msg.timestamp + IST).strftime("%H:%M")
        }))

    # Notify others user joined
    await manager.broadcast(room, {
        "type": "system",
        "message": f"{user.username} joined the chat"
    })

    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)
            message = msg_data.get("message", "").strip()
            if not message:
                continue

            # Save to DB
            db = SessionLocal()
            chat_msg = ChatMessage(
                user_id=user.id,
                username=user.username,
                message=message,
                room=room
            )
            db.add(chat_msg)
            db.commit()
            db.close()

            from datetime import timedelta
            IST = timedelta(hours=5, minutes=30)
            now_ist = (datetime.utcnow() + IST).strftime("%H:%M")

            await manager.broadcast(room, {
                "type": "message",
                "username": user.username,
                "message": message,
                "timestamp": now_ist
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        await manager.broadcast(room, {
            "type": "system",
            "message": f"{user.username} left the chat"
        })

@app.get("/chat-page")
def chat_page():
    return FileResponse("chat.html")

@app.get("/chat/history/{room}")
def chat_history(room: str, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    from datetime import timedelta
    IST = timedelta(hours=5, minutes=30)
    messages = db.query(ChatMessage).filter(
        ChatMessage.room == room
    ).order_by(ChatMessage.timestamp.desc()).limit(50).all()
    db.close()
    return [{"username": m.username, "message": m.message,
             "timestamp": (m.timestamp + IST).strftime("%d %b %H:%M"),
             "is_me": m.user_id == user.id} for m in reversed(messages)]

@app.get("/")
def dashboard():
    return FileResponse("dashboard.html")

@app.get("/teams-page")
def teams_page():
    return FileResponse("team.html")

@app.get("/login-page")
def login_page():
    return FileResponse("login.html")

@app.get("/horoscope")
def project_horoscope(token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    tasks = db.query(Task).filter(Task.user_id == user.id).all()
    db.close()
    try:
        from ai_brain import generate_horoscope
        horoscope = generate_horoscope(tasks, user.username)
        return {"horoscope": horoscope}
    except Exception as e:
        return {"horoscope": f"Error: {str(e)}"}

@app.get("/test-email")
def test_email():
    from notifier import send_email
    result = send_email("scholarship1540@gmail.com", "Test Email", "Railway email test working!")
    return {"result": str(result)}

# ─── COMMENTS ROUTES ───────────────────────────────────────────
class CommentCreate(BaseModel):
    content: str

@app.post("/tasks/{task_id}/comments")
def add_comment(task_id: int, comment: CommentCreate, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    from models import Comment
    new_comment = Comment(task_id=task_id, user_id=user.id, content=comment.content)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    db.close()
    return {"message": "Comment added", "id": new_comment.id, "content": new_comment.content, "created_at": str(new_comment.created_at)}

@app.get("/tasks/{task_id}/comments")
def get_comments(task_id: int, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    from models import Comment
    comments = db.query(Comment).filter(Comment.task_id == task_id).order_by(Comment.created_at.desc()).all()
    result = [{"id": c.id, "content": c.content, "created_at": str(c.created_at)} for c in comments]
    db.close()
    return result

@app.delete("/tasks/{task_id}/comments/{comment_id}")
def delete_comment(task_id: int, comment_id: int, token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    from models import Comment
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.user_id == user.id).first()
    if comment:
        db.delete(comment)
        db.commit()
    db.close()
    return {"message": "Deleted"}

# ─── ADVANCED ANALYTICS ────────────────────────────────────────
@app.get("/analytics/advanced")
def advanced_analytics_data(token: str = Cookie(None)):
    user = get_user_from_token(token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    db = SessionLocal()
    tasks = db.query(Task).filter(Task.user_id == user.id).all()
    db.close()
    now = datetime.utcnow()
    from datetime import timedelta

    weekly = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%a")
        completed = sum(1 for t in tasks if t.is_completed and t.due_date and
                       (day - timedelta(days=1)) <= t.due_date <= (day + timedelta(days=1)))
        weekly.append({"day": day_str, "completed": completed})

    client_stats = {}
    for t in tasks:
        c = t.client_name or "Unknown"
        if c not in client_stats:
            client_stats[c] = {"total": 0, "completed": 0, "overdue": 0}
        client_stats[c]["total"] += 1
        if t.is_completed:
            client_stats[c]["completed"] += 1
        elif t.due_date and t.due_date < now:
            client_stats[c]["overdue"] += 1

    total = len(tasks)
    completed = sum(1 for t in tasks if t.is_completed)
    overdue = sum(1 for t in tasks if not t.is_completed and t.due_date and t.due_date < now)
    urgent = sum(1 for t in tasks if not t.is_completed and t.due_date and 0 <= (t.due_date - now).days <= 3)

    return {
        "weekly": weekly,
        "client_stats": client_stats,
        "total": total,
        "completed": completed,
        "overdue": overdue,
        "urgent": urgent,
        "completion_rate": round((completed / total * 100) if total else 0, 1),
        "on_track": total - completed - overdue - urgent
    }
