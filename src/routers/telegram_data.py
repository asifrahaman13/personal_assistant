from typing import Optional

from fastapi import APIRouter, Depends, Query

from src.controllers.telegram_data_controller import TelegramDataController
from src.models.telegram_models import (
    GroupInfoRequest,
    GroupInfoResponse,
    GroupMessagesRequest,
    GroupMessagesResponse,
    LatestDetailedAnalysesResponse,
    LatestSentimentAnalysisResponse,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
)
from src.routers.auth_router import get_current_org

# Protected routes
telegram_data_router = APIRouter()
controller = TelegramDataController()


@telegram_data_router.post("/groups", response_model=GroupInfoResponse)
async def get_groups(request: GroupInfoRequest, current_org=Depends(get_current_org)):
    """Get user groups from Telegram"""
    return await controller.get_groups(request, current_org)


@telegram_data_router.post("/group-messages", response_model=GroupMessagesResponse)
async def group_messages(request: GroupMessagesRequest, current_org=Depends(get_current_org)):
    """Get messages from a specific group within a date range"""
    return await controller.get_group_messages(request, current_org)


@telegram_data_router.post("/sentiment-analysis", response_model=SentimentAnalysisResponse)
async def sentiment_analysis(
    request: SentimentAnalysisRequest, current_org=Depends(get_current_org)
):
    """Perform sentiment analysis on group messages"""
    return await controller.perform_sentiment_analysis(request, current_org)


@telegram_data_router.get(
    "/latest-sentiment-analysis", response_model=LatestSentimentAnalysisResponse
)
async def latest_sentiment_analysis(
    group_id: int = Query(..., description="Telegram group ID"),
    current_org=Depends(get_current_org),
):
    """Get the latest sentiment analysis for a group"""
    return await controller.get_latest_sentiment_analysis(group_id, current_org)


@telegram_data_router.get(
    "/latest-detailed-analyses", response_model=LatestDetailedAnalysesResponse
)
async def latest_detailed_analyses(
    limit: int = Query(100, description="Number of analyses to return (max 100)"),
    group_id: Optional[int] = Query(None, description="Filter by specific group ID"),
    current_org=Depends(get_current_org),
):
    """Get the latest detailed analyses"""
    return await controller.get_latest_detailed_analyses(limit, group_id, current_org)
