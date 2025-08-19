from fastapi import HTTPException

from src.core.email_task_manager import email_task_manager
from src.db.mongodb import MongoDBManager
from src.logs.logs import logger
from src.models.email_models import (
    EmailTaskRequest,
    EmailTaskResponse,
    EmailTasksListResponse,
    EmailTaskStatusResponse,
)

class EmailTasksController:
    def __init__(self):
        self.mongo_manager = MongoDBManager()

    async def start_email_task(self, request: EmailTaskRequest, current_org: dict) -> EmailTaskResponse:
        try:
            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            organization_id = organization["id"]

            result = await email_task_manager.start_email_task(
                organization_id=organization_id,
                email_address=request.email_addresses,
                filters=request.filters,
                app_password=organization.get("app_password", "")
            )

            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["message"])

            return EmailTaskResponse(
                success=True,
                message=result["message"],
                task_id=result["task_id"],
                email_addresses=result.get("email_addresses"),
                started_at=result.get("started_at"),
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error starting email task: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to start email task: {str(e)}"
            )

    async def stop_email_task(self, current_org: dict) -> EmailTaskResponse:
        try:
            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            organization_id = organization["id"]

            result = await email_task_manager.stop_email_task(organization_id)

            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["message"])

            return EmailTaskResponse(
                success=True, message=result["message"], task_id=result["task_id"]
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error stopping email task: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to stop email task: {str(e)}")

    async def get_email_task_status(self, current_org: dict) -> EmailTaskStatusResponse:
        try:
            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            organization_id = organization["id"]

            result = await email_task_manager.get_task_status(organization_id)

            if not result["success"]:
                return EmailTaskStatusResponse(success=False, message=result["message"]) # type: ignore

            return EmailTaskStatusResponse(
                success=True,
                task_id=result["task_id"],
                status=result["status"],
                email_addresses=result.get("email_addresses"),
                is_running=result.get("is_running"),
                started_at=result.get("started_at"),
                stopped_at=result.get("stopped_at"),
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting email task status: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get email task status: {str(e)}"
            )

    async def list_email_tasks(self, current_org: dict) -> EmailTasksListResponse:
        try:
            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            result = await email_task_manager.get_active_tasks()

            return EmailTasksListResponse(
                success=True,
                active_tasks=result["active_tasks"],
                total_active=result["total_active"],
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error listing email tasks: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to list email tasks: {str(e)}"
            )

    async def stop_all_email_tasks(self, current_org: dict) -> dict:
        try:
            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            result = await email_task_manager.stop_all_tasks()

            return {"success": True, "message": result["message"], "results": result["results"]}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error stopping all email tasks: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to stop all email tasks: {str(e)}"
            )