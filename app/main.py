from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.core.config import settings
import os

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered satellite change detection using NASA & ESA imagery",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

# Serve frontend if built
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

@app.on_event("startup")
async def startup():
    print(f"🛰  {settings.PROJECT_NAME} v{settings.VERSION} starting up")
    print(f"   Docs: http://{settings.HOST}:{settings.PORT}/docs")
