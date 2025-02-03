import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Freshflow API",
    description="API for managing Freshflow workflows",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers
app.include_router(workflow.router, prefix="/api", tags=["workflow"])

@app.on_event("startup")
async def startup_event():
    """Run startup tasks"""
    logger.info("Starting Freshflow API")

@app.on_event("shutdown")
async def shutdown_event():
    """Run cleanup tasks"""
    logger.info("Shutting down Freshflow API") 