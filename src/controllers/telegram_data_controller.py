from datetime import datetime
from typing import Optional

from fastapi import HTTPException

from src.core.analyzer import ProductionTelegramAnalyzer
from src.db.mongodb import MongoDBManager
from src.logs.logs import logger
from src.models.telegram_models import (
    GroupInfo,
    GroupInfoRequest,
    GroupInfoResponse,
    GroupMessage,
    GroupMessagesRequest,
    GroupMessagesResponse,
    LatestDetailedAnalysesResponse,
    LatestSentimentAnalysisResponse,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
)


class TelegramDataController:
    def __init__(self):
        self.mongo_manager = MongoDBManager()

    async def get_groups(self, request: GroupInfoRequest, current_org: dict) -> GroupInfoResponse:
        """Get user groups from Telegram"""
        phone = request.phone

        organization = await self.mongo_manager.find_one(
            "organizations", {"email": current_org["email"]}
        )
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        organization_id = organization["id"]
        analyzer = ProductionTelegramAnalyzer(organization_id=organization_id)

        if not await analyzer.validate_session(phone):
            if not await analyzer.login():
                raise HTTPException(status_code=401, detail="Failed to authenticate with Telegram")

        try:
            groups = await analyzer.get_user_groups()
            group_infos = [GroupInfo(**g) for g in groups]
            return GroupInfoResponse(
                success=True,
                message="Groups fetched successfully",
                groups=group_infos,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch groups: {str(e)}")

    async def get_group_messages(
        self, request: GroupMessagesRequest, current_org: dict
    ) -> GroupMessagesResponse:
        """Get messages from a specific group within a date range"""
        phone = request.phone
        group_id = request.group_id
        start_date = request.start_date
        end_date = request.end_date

        organization = await self.mongo_manager.find_one(
            "organizations", {"email": current_org["email"]}
        )
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        organization_id = organization["id"]
        analyzer = ProductionTelegramAnalyzer(organization_id=organization_id)

        if not await analyzer.validate_session(phone):
            if not await analyzer.login():
                raise HTTPException(status_code=401, detail="Failed to authenticate with Telegram")

        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            from datetime import timezone

            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            if len(end_date) == 10:
                end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

            group_info = await analyzer._get_group_info(group_id)
            if not group_info:
                raise HTTPException(
                    status_code=404,
                    detail=f"Could not find group information for group ID: {group_id}",
                )

            messages = await analyzer.get_group_messages_by_date_range(group_info, start_dt, end_dt)
            if not messages:
                return GroupMessagesResponse(
                    success=True,
                    message="No messages found in the date range",
                    messages=[],
                )

            formatted = [
                GroupMessage(
                    id=m["id"],
                    text=m["text"],
                    date=m["date"].isoformat()
                    if hasattr(m["date"], "isoformat")
                    else str(m["date"]),
                    sender_id=m["sender_id"],
                    sender_name=m["sender_name"] or "",
                )
                for m in messages
            ]
            return GroupMessagesResponse(
                success=True,
                message="Messages fetched successfully",
                messages=formatted,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fetching group messages failed: {str(e)}")

    async def perform_sentiment_analysis(
        self, request: SentimentAnalysisRequest, current_org: dict
    ) -> SentimentAnalysisResponse:
        """Perform sentiment analysis on group messages"""
        phone = request.phone
        group_id = request.group_id
        start_date = request.start_date
        end_date = request.end_date

        organization = await self.mongo_manager.find_one(
            "organizations", {"email": current_org["email"]}
        )
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        organization_id = organization["id"]
        analyzer = ProductionTelegramAnalyzer(organization_id=organization_id)

        try:
            result = await analyzer.perform_sentiment_analysis(
                phone=phone,
                group_id=group_id,
                start_date=start_date,
                end_date=end_date,
                max_concurrent=50,
            )

            return SentimentAnalysisResponse(
                success=result["success"],
                message=result["message"],
                analysis=result["analysis"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_latest_sentiment_analysis(
        self, group_id: int, current_org: dict
    ) -> LatestSentimentAnalysisResponse:
        """Get the latest sentiment analysis for a group"""
        organization = await self.mongo_manager.find_one(
            "organizations", {"email": current_org["email"]}
        )
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        organization_id = organization["id"]
        analyzer = ProductionTelegramAnalyzer(organization_id=organization_id)

        try:
            result = await analyzer.get_latest_sentiment_analysis(group_id)

            return LatestSentimentAnalysisResponse(
                success=result["success"],
                analysis=result["analysis"],
                _id=result["_id"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_latest_detailed_analyses(
        self, limit: int, group_id: Optional[int], current_org: dict
    ) -> LatestDetailedAnalysesResponse:
        """Get the latest detailed analyses"""
        if group_id is not None:
            group_id = int(group_id)

        if limit > 100:
            limit = 100

        organization = await self.mongo_manager.find_one(
            "organizations", {"email": current_org["email"]}
        )
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        organization_id = organization["id"]
        analyzer = ProductionTelegramAnalyzer(organization_id=organization_id)

        try:
            result = await analyzer.get_latest_detailed_analyses(
                limit=limit, group_id=int(group_id) if group_id is not None else 0
            )

            logger.info(f"Result of detailed analysis: {result}")

            return LatestDetailedAnalysesResponse(
                success=result["success"],
                message="Latest detailed analyses fetched successfully",
                analyses=result["analysis"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
