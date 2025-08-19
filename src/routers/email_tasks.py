from fastapi import APIRouter, Depends

from src.controllers.email_tasks_controller import EmailTasksController
from src.models.email_models import (
    EmailTaskRequest,
    EmailTaskResponse,
    EmailTasksListResponse,
    EmailTaskStatusResponse,
)
from src.routers.auth_router import get_current_org

email_tasks_router = APIRouter()
controller = EmailTasksController()


@email_tasks_router.post("/start", response_model=EmailTaskResponse)
async def start_email_task(request: EmailTaskRequest, current_org=Depends(get_current_org)):
    return await controller.start_email_task(request, current_org)


@email_tasks_router.delete("/stop", response_model=EmailTaskResponse)
async def stop_email_task(current_org=Depends(get_current_org)):
    return await controller.stop_email_task(current_org)


@email_tasks_router.get("/status", response_model=EmailTaskStatusResponse)
async def get_email_task_status(current_org=Depends(get_current_org)):
    return await controller.get_email_task_status(current_org)


@email_tasks_router.get("/list", response_model=EmailTasksListResponse)
async def list_email_tasks(current_org=Depends(get_current_org)):
    return await controller.list_email_tasks(current_org)


@email_tasks_router.delete("/stop-all")
async def stop_all_email_tasks(current_org=Depends(get_current_org)):
    """Stop all active email tasks (admin only)"""
    return await controller.stop_all_email_tasks(current_org)
