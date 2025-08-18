from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers.auth_router import auth_router
from src.routers.background_tasks import background_tasks_router
from src.routers.organization_router import organization_router
from src.routers.telegram_data import telegram_data_router

app = FastAPI(
    title="Telegram Analyzer API",
    description="API for Telegram group analysis and real-time message handling",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
app.include_router(organization_router, prefix="/api/v1", tags=["Organizations"])
app.include_router(telegram_data_router, prefix="/api/v1", tags=["Telegram Data"])
app.include_router(
    background_tasks_router, prefix="/api/v1/background-tasks", tags=["Background Tasks"]
)


@app.get("/")
async def root():
    return {"message": "Telegram Analyzer API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
