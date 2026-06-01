from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from models import SessionLocal, Task
from notifier import send_email

def check_deadlines():
    db = SessionLocal()
    now = datetime.utcnow()
    tasks = db.query(Task).filter(Task.is_completed == False).all()

    for task in tasks:
        days_left = (task.due_date - now).days

        # 3-day warning
        if days_left <= 3 and not task.alert_3day_sent:
            send_email(
                task.client_email,
                f"Reminder: '{task.title}' is due in 3 days",
                f"Hi {task.client_name},\n\nJust a reminder that '{task.title}' is due on {task.due_date.strftime('%Y-%m-%d')}.\n\nPlease complete it or reach out if you need help."
            )
            task.alert_3day_sent = True
            print(f"3-day alert sent to {task.client_email}")

        # 1-day warning
        if days_left <= 1 and not task.alert_1day_sent:
            send_email(
                task.client_email,
                f"URGENT: '{task.title}' is due tomorrow!",
                f"Hi {task.client_name},\n\nThis is an urgent reminder — '{task.title}' is due TOMORROW ({task.due_date.strftime('%Y-%m-%d')}).\n\nPlease confirm completion immediately."
            )
            task.alert_1day_sent = True
            print(f"1-day alert sent to {task.client_email}")

    db.commit()
    db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_deadlines, 'interval', hours=1)
    scheduler.start()
    return scheduler