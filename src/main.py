import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.routers import (
    auth_router,
    background_tasks_router,
    email_tasks_router,
    organization_router,
)

app = FastAPI(
    title="Personal Assistant API",
    description="API for Personal assistant and real-time message handling",
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
app.include_router(
    background_tasks_router, prefix="/api/v1/background-tasks", tags=["Background Tasks"]
)
app.include_router(email_tasks_router, prefix="/api/v1/email-tasks", tags=["Email Tasks"])


@app.get("/")
async def root():
    return JSONResponse(content={"message": "Personal Assistant API is running"})


@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"})


async def main():
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, reload=True)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
