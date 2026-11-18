from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = "client"

class UserCreate(UserBase):
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ClientBase(BaseModel):
    business_name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    business_description: Optional[str] = None
    target_audience: Optional[str] = None
    competitors: Optional[str] = None
    brand_voice: Optional[str] = None
    marketing_goals: Optional[str] = None
    social_media_links: Optional[Dict[str, str]] = None

class ClientCreate(ClientBase):
    pass

class ClientResponse(ClientBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowTrigger(BaseModel):
    client_id: int
    service_requested: str
    target_topic: Optional[str] = ""
