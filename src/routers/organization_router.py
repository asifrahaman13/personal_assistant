from fastapi import APIRouter, Depends

from src.controllers.organization_controller import OrganizationController
from src.models.telegram_models import (
    Organization,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from src.routers.auth_router import get_current_org

organization_router = APIRouter(dependencies=[Depends(get_current_org)])
controller = OrganizationController()


@organization_router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(org_data: OrganizationCreate, current_org=Depends(get_current_org)):
    return await controller.create_organization(org_data, current_org)


@organization_router.get("/organizations", response_model=list[Organization])
async def list_organizations():
    return await controller.list_organizations()


@organization_router.get("/organizations/{org_id}", response_model=Organization)
async def get_organization(org_id: str):
    return await controller.get_organization(org_id)


@organization_router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(org_id: str, org_data: OrganizationUpdate):
    return await controller.update_organization(org_id, org_data)


@organization_router.get("/check")
async def check_organization_setup(current_org=Depends(get_current_org)):
    return await controller.check_organization_setup(current_org)


@organization_router.delete("/organizations/{org_id}", response_model=OrganizationResponse)
async def delete_organization(org_id: str):
    return await controller.delete_organization(org_id)
