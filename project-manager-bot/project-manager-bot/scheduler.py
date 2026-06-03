from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from models import SessionLocal, Task, User
from notifier import send_email
from whatsapp_notifier import send_whatsapp

IST_OFFSET = timedelta(hours=5, minutes=30)
OWNER_WHATSAPP = "+918277415992"

def check_deadlines():
    db = SessionLocal()
    now = datetime.utcnow() + IST_OFFSET
    tasks = db.query(Task).filter(Task.is_completed == False).all()
    print(f"[Scheduler] Checking at IST: {now.strftime('%Y-%m-%d %H:%M')}")

    for task in tasks:
        due_ist = task.due_date + IST_OFFSET
        days_left = (due_ist - now).days

        # Get task owner email
        owner = db.query(User).filter(User.id == task.user_id).first()
        owner_email = owner.email if owner else None

        print(f"  {task.title} | days_left: {days_left} | owner: {owner_email}")

        if days_left <= 3 and not task.alert_3day_sent:
            # Email to client
            send_email(
                task.client_email,
                f"Reminder: {task.title} due in {days_left} days",
                f"Hi {task.client_name},\n\n{task.title} is due on {due_ist.strftime('%Y-%m-%d')}. Please complete it soon."
            )
            # Email copy to task owner
            if owner_email and owner_email != task.client_email:
                send_email(
                    owner_email,
                    f"[Your Task] Reminder: {task.title} due in {days_left} days",
                    f"Hi,\n\nYour task '{task.title}' for client {task.client_name} is due on {due_ist.strftime('%Y-%m-%d')}.\n\nThis is an automatic reminder from your Project Manager Bot."
                )
                print(f"  Owner copy sent to {owner_email}")
            # WhatsApp to owner
            send_whatsapp(
                OWNER_WHATSAPP,
                f"📋 REMINDER\nTask: {task.title}\nClient: {task.client_name}\nDue: {due_ist.strftime('%Y-%m-%d')}\n⏳ {days_left} days left!"
            )
            task.alert_3day_sent = True
            print(f"  SENT 3-day alert for {task.title}")

        if days_left <= 1 and not task.alert_1day_sent:
            # Email to client
            send_email(
                task.client_email,
                f"URGENT: {task.title} due tomorrow!",
                f"Hi {task.client_name},\n\n{task.title} is due TOMORROW {due_ist.strftime('%Y-%m-%d')}. Please act now."
            )
            # Email copy to task owner
            if owner_email and owner_email != task.client_email:
                send_email(
                    owner_email,
                    f"[Your Task] URGENT: {task.title} due tomorrow!",
                    f"Hi,\n\nUrgent! Your task '{task.title}' for client {task.client_name} is due TOMORROW {due_ist.strftime('%Y-%m-%d')}.\n\nTake action now!"
                )
                print(f"  Owner urgent copy sent to {owner_email}")
            # WhatsApp to owner
            send_whatsapp(
                OWNER_WHATSAPP,
                f"🚨 URGENT\nTask: {task.title}\nClient: {task.client_name}\nDue: TOMORROW {due_ist.strftime('%Y-%m-%d')}\nTake action now!"
            )
            task.alert_1day_sent = True
            print(f"  SENT 1-day alert for {task.title}")

    db.commit()
    db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_deadlines, "interval", hours=1)
    scheduler.start()
    return scheduler
