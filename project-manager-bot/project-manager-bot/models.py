from sqlalchemy import Column, Integer, String, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    client_name = Column(String)
    client_email = Column(String)
    due_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    alert_3day_sent = Column(Boolean, default=False)
    alert_1day_sent = Column(Boolean, default=False)

Base.metadata.create_all(engine)