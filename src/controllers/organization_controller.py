from datetime import datetime, timezone
from typing import List
import uuid

from fastapi import HTTPException

from src.db.mongodb import MongoDBManager
from src.logs.logs import logger
from src.models.telegram_models import (
    Organization,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)


class OrganizationController:
    def __init__(self):
        self.mongo_manager = MongoDBManager()

    async def create_organization(
        self, org_data: OrganizationCreate, current_org: dict
    ) -> OrganizationResponse:
        try:
            logger.info(f"The org_data is {org_data}")
            existing_org = await self.mongo_manager.find_one(
                "organizations", {"name": org_data.name}
            )
            if existing_org:
                raise HTTPException(
                    status_code=400,
                    detail="Organization with this name already exists",
                )

            org_id = str(uuid.uuid4())
            org_doc = {
                "id": org_id,
                "name": org_data.name,
                "api_id": org_data.api_id,
                "api_hash": org_data.api_hash,
                "app_password": org_data.app_password,
                "phone": org_data.phone,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }

            await self.mongo_manager.update_one(
                "organizations",
                {"email": current_org["email"]},
                org_doc,
                upsert=True,
            )

            return OrganizationResponse(
                success=True,
                message="Organization created successfully",
                organization_id=org_id,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def list_organizations(self) -> List[Organization]:
        try:
            organizations = await self.mongo_manager.find_many("organizations")
            return [Organization(**org) for org in organizations]

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error listing organizations: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def get_organization(self, org_id: str) -> Organization:
        try:
            org = await self.mongo_manager.find_one("organizations", {"id": org_id})
            if not org:
                raise HTTPException(status_code=404, detail="Organization not found")

            return Organization(**org)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting organization: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def update_organization(
        self, org_id: str, org_data: OrganizationUpdate
    ) -> OrganizationResponse:
        try:
            existing_org = await self.mongo_manager.find_one("organizations", {"id": org_id})
            if not existing_org:
                raise HTTPException(status_code=404, detail="Organization not found")

            update_data = {"updated_at": datetime.now(timezone.utc)}
            if org_data.name is not None:
                update_data["name"] = org_data.name  # type: ignore
            if org_data.api_id is not None:
                update_data["api_id"] = org_data.api_id  # type: ignore
            if org_data.api_hash is not None:
                update_data["api_hash"] = org_data.api_hash  # type: ignore
            if org_data.phone is not None:
                update_data["phone"] = org_data.phone  # type: ignore

            if await self.mongo_manager.update_one("organizations", {"id": org_id}, update_data):
                logger.info(f"Updated organization: {org_id}")
                return OrganizationResponse(
                    success=True,
                    message="Organization updated successfully",
                    organization_id=org_id,
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to update organization")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating organization: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def check_organization_setup(self, current_org: dict) -> dict:
        try:
            org = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            logger.info(f"The org is {org}")

            if not org:
                return {"is_setup": False, "message": "Organization not found"}

            has_api_credentials = org.get("api_id") and org.get("api_hash") and org.get("phone")

            return {
                "is_setup": has_api_credentials,
                "message": "Organization setup check completed",
            }

        except Exception as e:
            logger.error(f"Error checking organization setup: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def delete_organization(self, org_id: str) -> OrganizationResponse:
        try:
            if not await self.mongo_manager.setup():
                raise HTTPException(status_code=500, detail="Failed to setup database connection")

            existing_org = await self.mongo_manager.find_one("organizations", {"id": org_id})
            if not existing_org:
                raise HTTPException(status_code=404, detail="Organization not found")

            await self.mongo_manager.delete_one("organizations", {"id": org_id})
            await self.mongo_manager.delete_many("sessions", {"organization_id": org_id})
            await self.mongo_manager.delete_many("groups", {"organization_id": org_id})
            await self.mongo_manager.delete_many("messages", {"organization_id": org_id})
            await self.mongo_manager.delete_many("auth_sessions", {"organization_id": org_id})

            logger.info(f"Deleted organization: {org_id}")
            return OrganizationResponse(
                success=True,
                message="Organization deleted successfully",
                organization_id=org_id,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting organization: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
