from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class EmailTaskRequest(BaseModel):
    filters: Optional[List[str]] = None  # e.g., subject contains, sender, etc.


class EmailTaskResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[str] = None
    email_address: Optional[str] = None
    started_at: Optional[datetime] = None


class EmailTaskStatusResponse(BaseModel):
    success: bool
    task_id: Optional[str] = None
    status: Optional[str] = None
    email_address: Optional[str] = None
    is_running: Optional[bool] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None


class EmailTasksListResponse(BaseModel):
    success: bool
    active_tasks: dict
    total_active: int
