from datetime import datetime, timedelta

IST_OFFSET = timedelta(hours=5, minutes=30)

def analyze_risk(task):
    now = datetime.utcnow() + IST_OFFSET
    due_ist = task.due_date + IST_OFFSET
    days_left = (due_ist - now).days

    if task.is_completed:
        return {"level": "none", "label": "✅ Completed", "color": "gray"}
    elif days_left < 0:
        return {"level": "high", "label": f"🔴 HIGH RISK — Overdue by {abs(days_left)} days", "color": "red"}
    elif days_left == 0:
        return {"level": "high", "label": "🔴 HIGH RISK — Due today!", "color": "red"}
    elif days_left <= 3:
        return {"level": "medium", "label": f"🟡 MEDIUM RISK — Only {days_left} days left", "color": "orange"}
    elif days_left <= 7:
        return {"level": "low", "label": f"🟢 LOW RISK — {days_left} days left", "color": "green"}
    else:
        return {"level": "safe", "label": f"🟢 ON TRACK — {days_left} days left", "color": "green"}
