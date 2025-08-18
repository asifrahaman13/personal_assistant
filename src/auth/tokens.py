from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt as pyjwt
from passlib.context import CryptContext

from src.config.config import config
from src.db.mongodb import MongoDBManager
from src.logs.logs import logger

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

mongo_manager = MongoDBManager()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    import datetime

    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = pyjwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = pyjwt.decode(token, config.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except pyjwt.PyJWTError:
        return None


async def get_current_org(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    logger.info(f"The payload is {payload}")
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    org_email = payload["sub"]
    logger.info(f"The org_email is {org_email}")
    org = await mongo_manager.find_one("organizations", {"email": org_email})
    if not org:
        raise HTTPException(status_code=401, detail="Organization not found")
    logger.info(f"The org is {org}")
    return org
