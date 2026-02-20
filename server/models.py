from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON, func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="admin")

class GlobalConfig(Base):
    __tablename__ = "global_config"
    id = Column(Integer, primary_key=True, index=True)
    retention_days = Column(Integer, default=30) # Default to 30 days

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, unique=True, index=True)
    ip_address = Column(String)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    config = Column(JSON, default={}) # Store remote config here

    activities = relationship("ActivityLog", back_populates="agent")
    screenshots = relationship("Screenshot", back_populates="agent")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    log_type = Column(String) # "window", "url", "idle", "keystroke"
    content = Column(JSON) # Structured data: {"title": "...", "duration": ...}

    agent = relationship("Agent", back_populates="activities")

class Screenshot(Base):
    __tablename__ = "screenshots"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    file_path = Column(String)

    agent = relationship("Agent", back_populates="screenshots")
