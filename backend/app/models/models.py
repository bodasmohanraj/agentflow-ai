import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.db.session import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CLIENT = "client"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default=UserRole.CLIENT.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    website = Column(String, nullable=True)
    business_description = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    competitors = Column(Text, nullable=True)
    brand_voice = Column(String, nullable=True)
    marketing_goals = Column(Text, nullable=True)
    social_media_links = Column(JSON, nullable=True)
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="active")
    client_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    task = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    output = Column(JSON, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    token_usage = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, default="pending")
    client_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
