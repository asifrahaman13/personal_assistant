import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.core.tasks.realtime_intelligence import RealTimeIntelligenceHandler
from src.db.mongodb import MongoDBManager
from src.logs.logs import logger


class BackgroundTaskManager:
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_handlers: Dict[str, RealTimeIntelligenceHandler] = {}
        self.mongo_manager = MongoDBManager()

    async def start_intelligence_task(
        self, organization_id: str, group_ids: Optional[list] = None
    ) -> Dict[str, Any]:
        try:
            if organization_id in self.active_tasks:
                return {
                    "success": False,
                    "message": f"Background task already running for organization {organization_id}",
                    "task_id": organization_id,
                }

            handler = RealTimeIntelligenceHandler(organization_id=organization_id)

            if not await handler.setup_client():
                return {"success": False, "message": "Failed to setup Telegram client"}

            if group_ids:
                handler.clear_allowed_groups()
                for group_id in group_ids:
                    handler.add_allowed_group(group_id)
                logger.info(f"Added {len(group_ids)} specific groups to monitoring")
            else:
                handler.clear_allowed_groups()
                logger.info("Monitoring all groups")

            task = asyncio.create_task(self._run_intelligence_task(organization_id, handler))
            self.active_tasks[organization_id] = task
            self.task_handlers[organization_id] = handler

            task_info = {
                "organization_id": organization_id,
                "group_ids": group_ids or [],
                "status": "running",
                "started_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
            }

            await self.mongo_manager.update_one(
                "background_tasks", {"organization_id": organization_id}, task_info, upsert=True
            )

            logger.info(f"Started background intelligence task for organization {organization_id}")

            return {
                "success": True,
                "message": f"Background intelligence task started for organization {organization_id}",
                "task_id": organization_id,
                "group_ids": group_ids or [],
                "started_at": task_info["started_at"],
            }

        except Exception as e:
            logger.error(f"Error starting background task: {str(e)}")
            return {"success": False, "message": f"Failed to start background task: {str(e)}"}

    async def stop_intelligence_task(self, organization_id: str) -> Dict[str, Any]:
        try:
            if organization_id not in self.active_tasks:
                return {
                    "success": False,
                    "message": f"No active background task found for organization {organization_id}",
                }

            task = self.active_tasks[organization_id]
            task.cancel()

            handler = self.task_handlers.get(organization_id)
            if handler:
                await handler.stop_listening()
                del self.task_handlers[organization_id]

            del self.active_tasks[organization_id]

            await self.mongo_manager.update_one(
                "background_tasks",
                {"organization_id": organization_id},
                {"status": "stopped", "stopped_at": datetime.now(timezone.utc)},
            )

            logger.info(f"Stopped background intelligence task for organization {organization_id}")

            return {
                "success": True,
                "message": f"Background intelligence task stopped for organization {organization_id}",
                "task_id": organization_id,
            }

        except Exception as e:
            logger.error(f"Error stopping background task: {str(e)}")
            return {"success": False, "message": f"Failed to stop background task: {str(e)}"}

    async def _run_intelligence_task(
        self, organization_id: str, handler: RealTimeIntelligenceHandler
    ):
        try:
            logger.info(f"Starting intelligence task for organization {organization_id}")
            await handler.start_listening()
        except asyncio.CancelledError:
            logger.info(f"Intelligence task cancelled for organization {organization_id}")
        except Exception as e:
            logger.error(f"Error in intelligence task for organization {organization_id}: {str(e)}")
        finally:
            await self.mongo_manager.update_one(
                "background_tasks",
                {"organization_id": organization_id},
                {"status": "stopped", "stopped_at": datetime.now(timezone.utc)},
            )

    async def get_active_tasks(self) -> Dict[str, Any]:
        active_tasks = {}
        for org_id, _ in self.active_tasks.items():
            handler = self.task_handlers.get(org_id)
            active_tasks[org_id] = {
                "task_id": org_id,
                "status": "running",
                "allowed_groups": handler.get_allowed_groups() if handler else [],
                "is_running": handler.is_running if handler else False,
            }

        return {"success": True, "active_tasks": active_tasks, "total_active": len(active_tasks)}

    async def get_task_status(self, organization_id: str) -> Dict[str, Any]:
        try:
            if organization_id in self.active_tasks:
                handler = self.task_handlers.get(organization_id)
                return {
                    "success": True,
                    "task_id": organization_id,
                    "status": "running",
                    "allowed_groups": handler.get_allowed_groups() if handler else [],
                    "is_running": handler.is_running if handler else False,
                }
            else:
                task_info = await self.mongo_manager.find_one(
                    "background_tasks", {"organization_id": organization_id}
                )

                if task_info:
                    return {
                        "success": True,
                        "task_id": organization_id,
                        "status": task_info.get("status", "unknown"),
                        "started_at": task_info.get("started_at"),
                        "stopped_at": task_info.get("stopped_at"),
                    }
                else:
                    return {
                        "success": False,
                        "message": f"No task found for organization {organization_id}",
                    }

        except Exception as e:
            logger.error(f"Error getting task status: {str(e)}")
            return {"success": False, "message": f"Failed to get task status: {str(e)}"}

    async def stop_all_tasks(self) -> Dict[str, Any]:
        results = []
        for org_id in list(self.active_tasks.keys()):
            result = await self.stop_intelligence_task(org_id)
            results.append(result)

        return {
            "success": True,
            "message": f"Stopped {len(results)} background tasks",
            "results": results,
        }


background_task_manager = BackgroundTaskManager()
