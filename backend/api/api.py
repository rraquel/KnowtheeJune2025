from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.services import talent_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="KnowThee AI API",
    description="AI-powered talent analytics and employee insights platform",
    version="1.0.0"
)

# Configure CORS with more secure settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit default
        "http://127.0.0.1:8501",  # Streamlit alternative
        "http://localhost:3000",  # React default
        "http://127.0.0.1:3000",  # React alternative
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

app.include_router(talent_router, prefix="/api/talent")

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"status": "ok", "service": "KnowThee AI API"}

# Additional health check endpoint
@app.get("/health")
async def health():
    """Detailed health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "KnowThee AI API",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy") 