from fastapi import HTTPException

from src.core import background_task_manager
from src.db.mongodb import MongoDBManager
from src.logs.logs import logger
from src.models.telegram_models import (
    BackgroundTaskRequest,
    BackgroundTaskResponse,
    BackgroundTasksListResponse,
    BackgroundTaskStatusResponse,
)


class BackgroundTasksController:
    def __init__(self):
        self.mongo_manager = MongoDBManager()

    async def start_background_task(
        self, request: BackgroundTaskRequest, current_org: dict
    ) -> BackgroundTaskResponse:
        try:
            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            organization_id = organization["id"]

            result = await background_task_manager.start_intelligence_task(
                organization_id=organization_id, group_ids=request.group_ids
            )

            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["message"])

            return BackgroundTaskResponse(
                success=True,
                message=result["message"],
                task_id=result["task_id"],
                group_ids=result.get("group_ids"),
                started_at=result.get("started_at"),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error starting background task: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to start background task: {str(e)}"
            )

    async def stop_background_task(self, current_org: dict) -> BackgroundTaskResponse:
        try:
            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            organization_id = organization["id"]

            result = await background_task_manager.stop_intelligence_task(organization_id)

            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["message"])

            return BackgroundTaskResponse(
                success=True, message=result["message"], task_id=result["task_id"]
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error stopping background task: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to stop background task: {str(e)}")

    async def get_background_task_status(self, current_org: dict) -> BackgroundTaskStatusResponse:
        try:
            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            organization_id = organization["id"]

            result = await background_task_manager.get_task_status(organization_id)

            if not result["success"]:
                return BackgroundTaskStatusResponse(success=False, message=result["message"])

            return BackgroundTaskStatusResponse(
                success=True,
                task_id=result["task_id"],
                status=result["status"],
                allowed_groups=result.get("allowed_groups"),
                is_running=result.get("is_running"),
                started_at=result.get("started_at"),
                stopped_at=result.get("stopped_at"),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting background task status: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get background task status: {str(e)}"
            )

    async def list_background_tasks(self, current_org: dict) -> BackgroundTasksListResponse:
        try:
            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            result = await background_task_manager.get_active_tasks()

            return BackgroundTasksListResponse(
                success=True,
                active_tasks=result["active_tasks"],
                total_active=result["total_active"],
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error listing background tasks: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to list background tasks: {str(e)}"
            )

    async def stop_all_background_tasks(self, current_org: dict) -> dict:
        try:
            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            result = await background_task_manager.stop_all_tasks()

            return {"success": True, "message": result["message"], "results": result["results"]}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error stopping all background tasks: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to stop all background tasks: {str(e)}"
            )

    async def get_tg_stats(self, current_org: dict) -> dict:
        try:
            mongo_manager = MongoDBManager()
            organization = await mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            organization_id = organization["id"]

            messages = await mongo_manager.find_many(
                "messages", {"organization_id": organization_id}
            )

            logger.info(f"The emalls are : {messages}")

            total_messages = len(messages)
            unique_senders = len(set(message.get("sender_id") for message in messages))
            replies_sent = sum(
                1 for message in messages if message.get("text")
            )  # adjust logic as needed

            dates = [message.get("created_at") for message in messages if message.get("created_at")]
            date_range = {
                "start": min(dates) if dates else None,  # type: ignore
                "end": max(dates) if dates else None,  # type: ignore
            }

            return {
                "success": True,
                "total_messages": total_messages,
                "unique_senders": unique_senders,
                "replies_sent": replies_sent,
                "date_range": date_range,
            }
        except Exception as e:
            logger.error(f"Error fetching tg messages stats: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch tg messages stats: {str(e)}"
            )
