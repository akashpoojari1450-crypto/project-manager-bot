from groq import Groq
from datetime import datetime, timedelta
import os

IST = timedelta(hours=5, minutes=30)

def get_client():
    return Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_task_context(tasks):
    now = datetime.utcnow()
    lines = []
    for t in tasks:
        days_left = (t.due_date - now).days
        if t.is_completed: status = "Completed"
        elif days_left < 0: status = f"Overdue by {abs(days_left)} days"
        elif days_left == 0: status = "Due Today"
        elif days_left <= 3: status = "Urgent"
        else: status = f"{days_left} days left"
        lines.append(f"- {t.title} | Client: {t.client_name} | Due: {(t.due_date+IST).strftime('%Y-%m-%d')} | Status: {status}")
    return "\n".join(lines) if lines else "No tasks."

def generate_daily_briefing(tasks, username):
    context = get_task_context(tasks)
    now_ist = (datetime.utcnow() + IST).strftime("%d %b %Y")
    response = get_client().chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a professional project manager assistant."},
            {"role": "user", "content": f"Daily briefing for {username} on {now_ist}.\n\nTasks:\n{context}\n\nInclude: summary, critical items, top 3 priorities, one tip. Under 200 words, use emojis."}
        ],
        max_tokens=400
    )
    return response.choices[0].message.content

def suggest_reschedule(task):
    now = datetime.utcnow()
    days_left = (task.due_date - now).days
    response = get_client().chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a project manager. Suggest realistic new deadlines concisely."},
            {"role": "user", "content": f"Task '{task.title}' for {task.client_name} is {'overdue by ' + str(abs(days_left)) + ' days' if days_left < 0 else 'due in ' + str(days_left) + ' days'}. Suggest a new deadline in 1-2 sentences."}
        ],
        max_tokens=100
    )
    return response.choices[0].message.content

def chat_with_tasks(tasks, username, user_message):
    context = get_task_context(tasks)
    response = get_client().chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": f"You are a helpful project manager assistant for {username}.\n\nTheir tasks:\n{context}\n\nBe concise and use emojis."},
            {"role": "user", "content": user_message}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content
