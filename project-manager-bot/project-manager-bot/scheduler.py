from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone
from models import SessionLocal, Task
from notifier import send_email

IST_OFFSET = timedelta(hours=5, minutes=30)

def check_deadlines():
    db = SessionLocal()
    now = datetime.utcnow() + IST_OFFSET  # Convert to IST
    tasks = db.query(Task).filter(Task.is_completed == False).all()

    print(f"[Scheduler] Checking deadlines at IST: {now.strftime('%Y-%m-%d %H:%M')}")

    for task in tasks:
        due_ist = task.due_date + IST_OFFSET
        days_left = (due_ist - now).days

        print(f"  Task: {task.title} | Due IST: {due_ist.strftime('%Y-%m-%d')} | Days left: {days_left}")

        # 3-day warning
        if days_left <= 3 and not task.alert_3day_sent:
            send_email(
                task.client_email,
                f"Reminder: '{task.title}' is due in {days_left} days",
                f"Hi {task.client_name},\n\nReminder that '{task.title}' is due on {due_ist.strftime('%Y-%m-%d')}.\n\nPlease complete it or reach out if you need help."
            )
            task.alert_3day_sent = True
            print(f"  ✅ 3-day alert sent to {task.client_email}")

        # 1-day warning
        if days_left <= 1 and not task.alert_1day_sent:
            send_email(
                task.client_email,
                f"URGENT: '{task.title}' is due tomorrow!",
                f"Hi {task.client_name},\n\nUrgent reminder — '{task.title}' is due TOMORROW ({due_ist.strftime('%Y-%m-%d')}).\n\nPlease confirm completion immediately."
            )
            task.alert_1day_sent = True
            print(f"  ✅ 1-day alert sent to {task.client_email}")

    db.commit()
    db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_deadlines, 'interval', hours=1)
    scheduler.start()
    return scheduler
