from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")

# SQLite-specific settings: allow use across threads (needed since the
# scheduler runs in a background thread separate from request handlers),
# and give a longer busy-timeout so a request that arrives while another
# connection briefly holds a write lock waits instead of failing fast.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    # WAL mode lets readers proceed while a writer is committing, instead
    # of blocking the whole file. This is the main fix for "dashboard
    # stuck on Loading..." when the scheduler is mid-write.
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL")
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    tasks = relationship("Task", back_populates="owner", foreign_keys="Task.user_id")
    teams_owned = relationship("Team", back_populates="owner")
    team_memberships = relationship("TeamMember", back_populates="user")

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="teams_owned")
    members = relationship("TeamMember", back_populates="team")
    tasks = relationship("Task", back_populates="team")

class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, default="member")  # owner or member
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    client_name = Column(String)
    client_email = Column(String)
    client_token = Column(String)
    due_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    alert_3day_sent = Column(Boolean, default=False)
    alert_1day_sent = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    owner = relationship("User", back_populates="tasks", foreign_keys=[user_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    team = relationship("Team", back_populates="tasks")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    username = Column(String)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    room = Column(String, default="general")

Base.metadata.create_all(engine)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
