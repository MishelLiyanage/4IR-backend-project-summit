"""
FastAPI HTTP server for the 4IR image processing backend.
This creates the 'app' instance that uvicorn can run.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import Application

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="4IR Backend API",
    description="Image processing and text extraction API with LLM integration",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the backend application
logger.info("Initializing 4IR Backend Application...")
backend_app = Application()
image_controller = backend_app.container.get_controller('image')
logger.info("Backend application initialized successfully")


# Pydantic models for request/response validation
class ImageUploadRequest(BaseModel):
    encoded_image: str
    media_type: str = "image/jpeg"


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic info."""
    return HealthResponse(
        status="healthy",
        service="4IR Backend API",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="4IR Backend API",
        version="1.0.0"
    )


@app.post("/images/extract-text")
async def extract_text(request: ImageUploadRequest):
    """
    Extract text from uploaded image using LLM service.
    
    Args:
        request: ImageUploadRequest containing base64 encoded image
        
    Returns:
        Extracted text and metadata
    """
    try:
        logger.info("Received image extraction request")
        
        # Convert Pydantic model to dict for controller
        request_data = {
            "encoded_image": request.encoded_image,
            "media_type": request.media_type
        }
        
        # Call the image controller
        result = await image_controller.extract_text(request_data)
        
        # Handle different response status codes
        status_code = result.get('status_code', 200)
        
        if status_code >= 400:
            raise HTTPException(
                status_code=status_code,
                detail=result.get('error', {})
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in extract_text: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error", "type": "InternalServerError"}
        )


@app.get("/images/health")
async def image_service_health():
    """Image service health check endpoint."""
    try:
        result = await image_controller.health_check()
        
        status_code = result.get('status_code', 200)
        if status_code >= 400:
            raise HTTPException(
                status_code=status_code,
                detail=result.get('error', {})
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Health check failed", "type": "HealthCheckError"}
        )


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting 4IR Backend API Server with uvicorn...")
    print("📱 Frontend can connect to: http://localhost:8000")
    print("🖼️  Image processing endpoint: POST /images/extract-text")
    print("💚 Health check: GET /health")
    print("📚 API docs available at: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)