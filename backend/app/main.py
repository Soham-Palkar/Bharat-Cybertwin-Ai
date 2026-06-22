import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
from .database import engine, Base
from .routers import assets, logs, simulate, incidents, ml, risk, huntgpt, containment, data_ingestion
from .services.synthetic_logs import run_synthetic_log_generator
from .services.detection import run_detection_background_loop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cybertwin")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    logger.info("Initializing database and creating tables...")
    Base.metadata.create_all(bind=engine)

    # Start background tasks if not running tests
    import os
    log_gen_task = None
    detection_task = None

    if os.getenv("TESTING") != "1":
        logger.info("Starting synthetic log generator background service...")
        log_gen_task = asyncio.create_task(run_synthetic_log_generator())
        logger.info("Starting detection engine background loop...")
        detection_task = asyncio.create_task(run_detection_background_loop())
    else:
        logger.info("TESTING environment detected. Skipping background services.")

    yield

    # Shutdown: Cancel background tasks
    logger.info("Shutting down background services...")
    for task, name in [(log_gen_task, "log generator"), (detection_task, "detection loop")]:
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Background {name} successfully stopped.")
    if not log_gen_task and not detection_task:
        logger.info("No active background services to stop.")

app = FastAPI(
    title="CyberTwin AI",
    description="AI-Powered Cybersecurity Digital Twin & SOC Copilot - Complete MVP (Modules 1–10)",
    version="1.1.0",
    lifespan=lifespan
)

# Register routers
app.include_router(assets.router, tags=["Assets"])
app.include_router(logs.router, tags=["Logs"])
app.include_router(simulate.router)
app.include_router(incidents.router)
app.include_router(ml.router)
app.include_router(risk.router)
app.include_router(huntgpt.router)
app.include_router(containment.router)
app.include_router(data_ingestion.router, tags=["Data Ingestion"])

@app.get("/")
def read_root():
    return {"message": "Welcome to CyberTwin AI API - MVP"}

