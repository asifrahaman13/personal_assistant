from fastapi import APIRouter, Depends

from src.auth.tokens import get_current_org
from src.controllers.auth_controller import AuthController
from src.models.telegram_models import (
    CodeRequest,
    CodeResponse,
    LoginResponse,
    OrganizationLoginRequest,
    OrganizationSignupRequest,
    Token,
)

# Public routes
auth_router = APIRouter()
controller = AuthController()


@auth_router.post("/signup", response_model=Token)
async def signup(org_data: OrganizationSignupRequest):
    """Organization signup endpoint"""
    return await controller.signup_organization(org_data)


@auth_router.post("/login", response_model=Token)
async def login(form_data: OrganizationLoginRequest):
    """Organization login endpoint"""
    return await controller.login_organization(form_data)


# Protected routes
@auth_router.post("/telegram-login", response_model=LoginResponse)
async def telegram_login(form_data: dict, current_org=Depends(get_current_org)):
    """Telegram login endpoint"""
    return await controller.telegram_login(form_data, current_org)


@auth_router.post("/code", response_model=CodeResponse)
async def verify_code(request: CodeRequest, current_org=Depends(get_current_org)):
    """Verify Telegram code endpoint"""
    return await controller.verify_code(request, current_org)


@auth_router.get("/logout/{organization_id}/{phone}")
async def logout(organization_id: str, phone: str):
    """Logout endpoint"""
    return await controller.logout(organization_id, phone)
