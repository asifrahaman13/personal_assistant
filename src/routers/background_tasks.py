from fastapi import APIRouter, Depends

from src.controllers.background_tasks_controller import BackgroundTasksController
from src.models.telegram_models import (
    BackgroundTaskRequest,
    BackgroundTaskResponse,
    BackgroundTasksListResponse,
    BackgroundTaskStatusResponse,
)
from src.routers.auth_router import get_current_org

# Protected routes
background_tasks_router = APIRouter()
controller = BackgroundTasksController()


@background_tasks_router.post("/start", response_model=BackgroundTaskResponse)
async def start_background_task(
    request: BackgroundTaskRequest, current_org=Depends(get_current_org)
):
    """Start a background task for real-time intelligence monitoring"""
    return await controller.start_background_task(request, current_org)


@background_tasks_router.delete("/stop", response_model=BackgroundTaskResponse)
async def stop_background_task(current_org=Depends(get_current_org)):
    """Stop the background task for the current organization"""
    return await controller.stop_background_task(current_org)


@background_tasks_router.get("/status", response_model=BackgroundTaskStatusResponse)
async def get_background_task_status(current_org=Depends(get_current_org)):
    """Get the status of the background task for the current organization"""
    return await controller.get_background_task_status(current_org)


@background_tasks_router.get("/list", response_model=BackgroundTasksListResponse)
async def list_background_tasks(current_org=Depends(get_current_org)):
    """Get information about all active background tasks (admin only)"""
    return await controller.list_background_tasks(current_org)


@background_tasks_router.delete("/stop-all")
async def stop_all_background_tasks(current_org=Depends(get_current_org)):
    """Stop all active background tasks (admin only)"""
    return await controller.stop_all_background_tasks(current_org)
