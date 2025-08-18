from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class Organization(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., description="Organization name")
    email: str = Field(..., description="Organization email (unique, used for login)")
    password_hash: str = Field(..., description="Hashed password")
    api_id: str = Field(..., description="Telegram API ID")
    api_hash: str = Field(..., description="Telegram API Hash")
    phone: str = Field(..., description="Phone number in international format")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OrganizationCreate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    name: str = Field(..., description="Organization name")
    api_id: str = Field(..., description="Telegram API ID")
    api_hash: str = Field(..., description="Telegram API Hash")
    phone: str = Field(..., description="Phone number in international format")


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    api_id: Optional[str] = None
    api_hash: Optional[str] = None
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    phone: str = Field(
        ...,
        description="Phone number in international format (e.g., +1234567890)",
    )


class CodeRequest(BaseModel):
    phone: str = Field(..., description="Phone number in international format")
    code: str = Field(..., description="Verification code received via Telegram")


class LoginResponse(BaseModel):
    success: bool
    message: str
    requires_code: bool = False


class CodeResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None


class OrganizationResponse(BaseModel):
    success: bool
    message: str
    organization_id: Optional[str] = None


class GroupInfoRequest(BaseModel):
    phone: str = Field(..., description="Phone number in international format")


class GroupInfo(BaseModel):
    id: int = Field(..., description="Group ID")
    title: str
    username: Optional[str]
    participants_count: int = 0


class GroupInfoResponse(BaseModel):
    success: bool
    message: str
    groups: list[GroupInfo] = []


class SentimentAnalysisRequest(BaseModel):
    phone: str = Field(..., description="Phone number in international format")
    group_id: int = Field(..., description="Telegram group ID")
    start_date: str = Field(..., description="Start date in ISO format (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date in ISO format (YYYY-MM-DD)")


class SentimentAnalysisResponse(BaseModel):
    success: bool
    message: str
    analysis: dict = {}


class GroupMessagesRequest(BaseModel):
    phone: str = Field(..., description="Phone number in international format")
    group_id: int = Field(..., description="Telegram group ID")
    start_date: str = Field(..., description="Start date in ISO format (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date in ISO format (YYYY-MM-DD)")


class GroupMessage(BaseModel):
    id: int
    text: str
    date: str
    sender_id: int
    sender_name: str


class GroupMessagesResponse(BaseModel):
    success: bool
    message: str
    messages: list[GroupMessage] = []


class LatestSentimentAnalysisResponse(BaseModel):
    success: bool = Field(...)
    analysis: dict = Field(...)
    _id: str | None = None


class OrganizationSignupRequest(BaseModel):
    email: str = Field(..., description="Organization email address")
    password: str = Field(..., description="Password for the organization account")


class OrganizationLoginRequest(BaseModel):
    email: str = Field(..., description="Organization email address")
    password: str = Field(..., description="Password for the organization account")


class Token(BaseModel):
    access_token: str
    token_type: str
    phone: Optional[str] = None


class DetailedAnalysisMessage(BaseModel):
    message_id: int
    text: str
    date: datetime
    sender_id: int
    sender_name: str
    sentiment: str
    polarity: float


class DetailedAnalysisSummary(BaseModel):
    total_messages: int
    unique_users: int
    average_sentiment: float
    sentiment_distribution: dict


class DetailedAnalysisUserActivity(BaseModel):
    user_message_counts: dict
    top_users: list


class DetailedAnalysis(BaseModel):
    organization_id: str
    group_id: int
    group_title: str
    analysis_date: datetime
    time_period_days: int
    summary: DetailedAnalysisSummary
    user_activity: DetailedAnalysisUserActivity
    messages_with_sentiment: list[DetailedAnalysisMessage]


class LatestDetailedAnalysesResponse(BaseModel):
    success: bool
    message: str
    analyses: DetailedAnalysis


class BackgroundTaskRequest(BaseModel):
    group_ids: Optional[list[int]] = Field(
        None,
        description="List of specific group IDs to monitor. If not provided, monitors all groups",
    )


class BackgroundTaskResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[str] = None
    group_ids: Optional[list[int]] = None
    started_at: Optional[datetime] = None


class BackgroundTaskStatusResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    task_id: Optional[str] = None
    status: Optional[str] = None
    allowed_groups: Optional[list[int]] = None
    is_running: Optional[bool] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None


class BackgroundTasksListResponse(BaseModel):
    success: bool
    active_tasks: Dict[str, dict] = {}
    total_active: int = 0
