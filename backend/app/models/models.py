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
    strategies = relationship("Strategy", order_by="Strategy.id", back_populates="client")

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

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    executive_summary = Column(Text, nullable=True)
    business_analysis = Column(Text, nullable=True)
    target_audience_personas = Column(Text, nullable=True)
    competitor_positioning = Column(Text, nullable=True)
    brand_positioning = Column(Text, nullable=True)
    marketing_objectives = Column(Text, nullable=True)
    recommended_channels = Column(Text, nullable=True)
    content_pillars = Column(Text, nullable=True)
    campaign_ideas = Column(Text, nullable=True)
    kpis_and_metrics = Column(JSON, nullable=True)
    thirty_day_action_plan = Column(Text, nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    client = relationship("Client", back_populates="strategies")
