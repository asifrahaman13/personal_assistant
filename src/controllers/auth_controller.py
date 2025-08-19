from datetime import datetime, timezone
from typing import Dict
import uuid

from fastapi import HTTPException

from src.auth.tokens import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from src.core.analyzer import ProductionTelegramAnalyzer
from src.db.mongodb import MongoDBManager
from src.logs.logs import logger
from src.models.telegram_models import (
    CodeRequest,
    CodeResponse,
    LoginResponse,
    OrganizationLoginRequest,
    OrganizationSignupRequest,
    Token,
)


class AuthController:
    def __init__(self):
        self.mongo_manager = MongoDBManager()
        self.pending_sessions: Dict[str, ProductionTelegramAnalyzer] = {}

    async def signup_organization(self, org_data: OrganizationSignupRequest) -> Token:
        existing = await self.mongo_manager.find_one("organizations", {"email": org_data.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        org_dict = org_data.model_dump()
        org_dict["password_hash"] = get_password_hash(org_dict.pop("password"))
        org_dict["id"] = str(uuid.uuid4())
        org_dict["created_at"] = datetime.now(timezone.utc)
        org_dict["updated_at"] = datetime.now(timezone.utc)

        if not await self.mongo_manager.insert_one("organizations", org_dict):
            raise HTTPException(status_code=500, detail="Failed to create organization")

        access_token = create_access_token({"sub": org_dict["email"], "id": org_dict["id"]})
        return Token(access_token=access_token, token_type="bearer")

    async def login_organization(self, form_data: OrganizationLoginRequest) -> Token:
        logger.info(f"The form_data is {form_data}")
        org = await self.mongo_manager.find_one("organizations", {"email": form_data.email})
        if not org or not verify_password(form_data.password, org["password_hash"]):
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        access_token = create_access_token({"sub": org["email"]})
        return Token(access_token=access_token, token_type="bearer", phone=org["phone"])

    async def telegram_login(self, form_data: dict, current_org: dict) -> LoginResponse:
        logger.info(f"The form_data is {form_data} {current_org}")
        org = await self.mongo_manager.find_one("organizations", {"email": current_org["email"]})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        logger.info(f"The org is {org}")
        analyzer = ProductionTelegramAnalyzer(organization_id=org["id"])
        await analyzer.send_code_request(form_data["phone"])

        session_key = f"{org['id']}:{form_data['phone']}"
        self.pending_sessions[session_key] = analyzer
        logger.info(f"The pending sessions are {self.pending_sessions}")

        return LoginResponse(
            success=True,
            requires_code=True,
            message="Successfully sent code",
        )

    async def verify_code(self, request: CodeRequest, current_org: dict) -> CodeResponse:
        try:
            logger.info(f"The request is {request}")
            logger.info(f"The current_org is {current_org}")

            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")
            organization_id = organization["id"]
            logger.info(f"The organization is {organization_id}")

            phone = request.phone
            code = request.code
            logger.info(f"The pending sessions are {self.pending_sessions}")

            session_key = f"{organization_id}:{phone}"
            if session_key not in self.pending_sessions:
                raise HTTPException(
                    status_code=400,
                    detail="No pending login session found. Please start login process again.",
                )

            pending_analyzer = self.pending_sessions[session_key]
            try:
                session_string = await pending_analyzer.verify_code(phone, code)

                if session_string:
                    if await pending_analyzer._save_session(phone, session_string):
                        logger.info(
                            f"Successfully authenticated user: {phone} for organization: {organization_id}"
                        )

                        del self.pending_sessions[session_key]
                        try:
                            await self.mongo_manager.delete_one(
                                "auth_sessions",
                                {
                                    "organization_id": organization_id,
                                    "phone": phone,
                                },
                            )
                        except Exception:
                            pass  # Ignore cleanup errors

                        if pending_analyzer.client:
                            await pending_analyzer.cleanup_client()  # type: ignore

                        return CodeResponse(
                            success=True,
                            message="Successfully authenticated",
                            session_id=session_string,
                        )
                    else:
                        raise HTTPException(status_code=500, detail="Failed to save session")
                else:
                    raise HTTPException(status_code=400, detail="Invalid verification code")

            except Exception as e:
                logger.error(f"Error during code verification: {e}")
                if session_key in self.pending_sessions:
                    del self.pending_sessions[session_key]
                try:
                    await self.mongo_manager.delete_one(
                        "auth_sessions",
                        {"organization_id": organization_id, "phone": phone},
                    )
                except Exception:
                    pass  # Ignore cleanup errors

                if pending_analyzer.client:
                    await pending_analyzer.cleanup_client()  # type: ignore
                raise HTTPException(status_code=400, detail=f"Code verification failed: {str(e)}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Code verification error: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def logout(self, organization_id: str, phone: str) -> dict:
        try:
            result = await self.mongo_manager.delete_one(
                "sessions", {"organization_id": organization_id, "phone": phone}
            )

            if result:
                return {"success": True, "message": "Successfully logged out"}
            else:
                return {"success": False, "message": "No session found to logout"}

        except Exception as e:
            logger.error(f"Logout error: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
