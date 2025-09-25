"""
Image controller implementation for handling image upload and text extraction.
"""

from typing import Dict, Any
import logging
from src.controllers import BaseController
from src.services.llm_service import LLMService
from src.dto import ImageUploadRequestDTO, TextExtractionResponseDTO
from src.exceptions import (
    ImageProcessingError, Base64ValidationError, ImageSizeError,
    UnsupportedImageTypeError, LLMServiceError, LLMServiceTimeoutError,
    TextExtractionError
)

logger = logging.getLogger(__name__)


class ImageController(BaseController):
    """Controller for image processing endpoints."""
    
    def __init__(self, llm_service: LLMService):
        """Initialize image controller with LLM service."""
        # Pass None as service since we're using LLM service directly
        super().__init__(None)
        self._llm_service = llm_service
    
    def get_routes(self) -> Dict[str, Any]:
        """Get image controller routes configuration."""
        return {
            "POST /images/extract-text": self.extract_text,
            "GET /images/health": self.health_check,
        }
    
    async def extract_text(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST request for text extraction from image."""
        try:
            logger.info("Processing image text extraction request")
            
            # Validate request data
            if 'encoded_image' not in request_data:
                return self._bad_request_response("Missing 'encoded_image' field")
            
            # Create DTO from request
            image_request = ImageUploadRequestDTO.from_dict(request_data)
            
            # Extract text using LLM service
            result = await self._llm_service.extract_text_from_image(image_request)
            
            logger.info("Text extraction completed successfully")
            return self._success_response(result.to_dict())
            
        except Base64ValidationError as e:
            logger.warning(f"Base64 validation error: {e}")
            return self._bad_request_response(str(e))
            
        except ImageSizeError as e:
            logger.warning(f"Image size error: {e}")
            return self._bad_request_response(str(e))
            
        except UnsupportedImageTypeError as e:
            logger.warning(f"Unsupported image type: {e}")
            return self._bad_request_response(str(e))
            
        except ImageProcessingError as e:
            logger.error(f"Image processing error: {e}")
            return self._bad_request_response(str(e))
            
        except LLMServiceTimeoutError as e:
            logger.error(f"LLM service timeout: {e}")
            return self._timeout_response(str(e))
            
        except LLMServiceError as e:
            logger.error(f"LLM service error: {e}")
            return self._service_unavailable_response(str(e))
            
        except TextExtractionError as e:
            logger.error(f"Text extraction error: {e}")
            return self._unprocessable_entity_response(str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error in text extraction: {e}")
            return self._error_response("An unexpected error occurred during text extraction")
    
    async def health_check(self) -> Dict[str, Any]:
        """Handle GET request for service health check."""
        try:
            logger.info("Processing health check request")
            
            health_status = self._llm_service.get_service_health()
            
            return self._success_response({
                "service": "image-processing",
                "status": "healthy",
                "llm_service": health_status,
                "capabilities": [
                    "text-extraction",
                    "base64-image-processing"
                ]
            })
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return self._error_response("Health check failed")
    
    def _timeout_response(self, message: str) -> Dict[str, Any]:
        """Create timeout response."""
        return {
            "status": "error",
            "status_code": 408,
            "error": {
                "message": message,
                "type": "RequestTimeout"
            }
        }
    
    def _service_unavailable_response(self, message: str) -> Dict[str, Any]:
        """Create service unavailable response."""
        return {
            "status": "error",
            "status_code": 503,
            "error": {
                "message": message,
                "type": "ServiceUnavailable"
            }
        }
    
    def _unprocessable_entity_response(self, message: str) -> Dict[str, Any]:
        """Create unprocessable entity response."""
        return {
            "status": "error",
            "status_code": 422,
            "error": {
                "message": message,
                "type": "UnprocessableEntity"
            }
        }
    
    # Override methods that depend on service since we don't use base service
    async def get_by_id(self, entity_id: str) -> Dict[str, Any]:
        """Not implemented for image controller."""
        return self._bad_request_response("Method not supported")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Not implemented for image controller."""
        return self._bad_request_response("Method not supported")
    
    async def create(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Redirect to extract_text method."""
        return await self.extract_text(entity_data)
    
    async def update(self, entity_id: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Not implemented for image controller."""
        return self._bad_request_response("Method not supported")
    
    async def delete(self, entity_id: str) -> Dict[str, Any]:
        """Not implemented for image controller."""
        return self._bad_request_response("Method not supported")