from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    role: str
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class AgentCreate(BaseModel):
    hostname: str
    ip_address: str

class AgentConfig(BaseModel):
    screenshot_interval: int = 60
    upload_interval: int = 300
    active_window_interval: int = 5

class ActivityLogCreate(BaseModel):
    log_type: str
    content: Dict[str, Any]
    timestamp: datetime

class ScreenshotCreate(BaseModel):
    timestamp: datetime
