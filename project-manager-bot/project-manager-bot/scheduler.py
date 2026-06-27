from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from models import SessionLocal, Task, User
from notifier import send_email
from whatsapp_notifier import send_whatsapp

IST_OFFSET = timedelta(hours=5, minutes=30)
OWNER_WHATSAPP = "+918277415992"

def check_deadlines():
    # Phase 1: quickly figure out which tasks need which alerts, and
    # collect everything we need to send those alerts. No network calls
    # happen in this phase, so the DB session (and any write lock) is
    # held for only a fraction of a second.
    db = SessionLocal()
    now = datetime.utcnow() + IST_OFFSET
    tasks = db.query(Task).filter(Task.is_completed == False).all()
    print(f"[Scheduler] Checking at IST: {now.strftime('%Y-%m-%d %H:%M')}")

    to_send_3day = []
    to_send_1day = []

    for task in tasks:
        due_ist = task.due_date + IST_OFFSET
        days_left = (due_ist - now).days
        owner = db.query(User).filter(User.id == task.user_id).first()
        owner_email = owner.email if owner else None

        print(f"  {task.title} | days_left: {days_left} | owner: {owner_email}")

        if days_left <= 3 and not task.alert_3day_sent:
            to_send_3day.append({
                "task_id": task.id,
                "title": task.title,
                "client_name": task.client_name,
                "client_email": task.client_email,
                "due_str": due_ist.strftime("%Y-%m-%d"),
                "days_left": days_left,
                "owner_email": owner_email,
            })

        if days_left <= 1 and not task.alert_1day_sent:
            to_send_1day.append({
                "task_id": task.id,
                "title": task.title,
                "client_name": task.client_name,
                "client_email": task.client_email,
                "due_str": due_ist.strftime("%Y-%m-%d"),
                "owner_email": owner_email,
            })

    db.close()

    # Phase 2: send emails/WhatsApp with NO database session open. These
    # are slow, blocking network calls (SMTP login, Twilio HTTP) - if the
    # DB session were still open here, every other request hitting the
    # same SQLite file would queue up behind this loop and the dashboard
    # would appear to hang on "Loading...".
    sent_3day_ids = []
    for t in to_send_3day:
        send_email(
            t["client_email"],
            f"Reminder: {t['title']} due in {t['days_left']} days",
            f"Hi {t['client_name']},\n\n{t['title']} is due on {t['due_str']}. Please complete it soon."
        )
        if t["owner_email"] and t["owner_email"] != t["client_email"]:
            send_email(
                t["owner_email"],
                f"[Your Task] Reminder: {t['title']} due in {t['days_left']} days",
                f"Hi,\n\nYour task '{t['title']}' for client {t['client_name']} is due on {t['due_str']}.\n\nThis is an automatic reminder from your Project Manager Bot."
            )
            print(f"  Owner copy sent to {t['owner_email']}")
        send_whatsapp(
            OWNER_WHATSAPP,
            f"📋 REMINDER\nTask: {t['title']}\nClient: {t['client_name']}\nDue: {t['due_str']}\n⏳ {t['days_left']} days left!"
        )
        print(f"  SENT 3-day alert for {t['title']}")
        sent_3day_ids.append(t["task_id"])

    sent_1day_ids = []
    for t in to_send_1day:
        send_email(
            t["client_email"],
            f"URGENT: {t['title']} due tomorrow!",
            f"Hi {t['client_name']},\n\n{t['title']} is due TOMORROW {t['due_str']}. Please act now."
        )
        if t["owner_email"] and t["owner_email"] != t["client_email"]:
            send_email(
                t["owner_email"],
                f"[Your Task] URGENT: {t['title']} due tomorrow!",
                f"Hi,\n\nUrgent! Your task '{t['title']}' for client {t['client_name']} is due TOMORROW {t['due_str']}.\n\nTake action now!"
            )
            print(f"  Owner urgent copy sent to {t['owner_email']}")
        send_whatsapp(
            OWNER_WHATSAPP,
            f"🚨 URGENT\nTask: {t['title']}\nClient: {t['client_name']}\nDue: TOMORROW {t['due_str']}\nTake action now!"
        )
        print(f"  SENT 1-day alert for {t['title']}")
        sent_1day_ids.append(t["task_id"])

    # Phase 3: flip the alert flags in a brief final session.
    if sent_3day_ids or sent_1day_ids:
        db = SessionLocal()
        if sent_3day_ids:
            db.query(Task).filter(Task.id.in_(sent_3day_ids)).update(
                {"alert_3day_sent": True}, synchronize_session=False
            )
        if sent_1day_ids:
            db.query(Task).filter(Task.id.in_(sent_1day_ids)).update(
                {"alert_1day_sent": True}, synchronize_session=False
            )
        db.commit()
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_deadlines, "interval", hours=1)
    scheduler.start()
    return scheduler
