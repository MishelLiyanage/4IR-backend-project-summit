"""
LLM service for communicating with Sysco Gen AI Platform.
"""

import logging
import time
import base64
import imghdr
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.constants import AppConfig, ValidationLimits, Messages
from src.exceptions import (
    LLMServiceError, LLMServiceTimeoutError, TextExtractionError,
    ImageProcessingError, Base64ValidationError, ImageSizeError,
    UnsupportedImageTypeError
)
from src.dto import (
    ImageUploadRequestDTO, LLMRequestDTO, LLMMediaDataDTO, 
    TextExtractionResponseDTO, LLMResponseDTO
)

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM communication and text extraction."""
    
    def __init__(self, config: AppConfig):
        """Initialize LLM service with configuration."""
        self.config = config
        self.llm_config = config.get_llm_config()
        self.session = self._create_http_session()
        
        logger.info(f"LLM Service initialized with endpoint: {self.llm_config['api_url']}")
    
    def _create_http_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.llm_config['max_retries'],
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    async def extract_text_from_image(self, image_request: ImageUploadRequestDTO) -> TextExtractionResponseDTO:
        """Extract text from base64 encoded image."""
        start_time = time.time()
        
        try:
            logger.info("Starting text extraction from image")
            
            # Validate image data
            self._validate_image_data(image_request)
            
            # Prepare LLM request
            llm_request = self._prepare_llm_request(image_request)
            
            # Call LLM service
            llm_response = await self._call_llm_service(llm_request)
            
            # Process response
            extracted_text = self._extract_text_from_response(llm_response)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            response = TextExtractionResponseDTO(
                extracted_text=extracted_text,
                processing_time_ms=processing_time,
                image_metadata={
                    'media_type': image_request.media_type,
                    'size_estimate': len(image_request.encoded_image)
                }
            )
            
            logger.info(f"Text extraction completed in {processing_time}ms")
            return response
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Text extraction failed after {processing_time}ms: {e}")
            raise
    
    def _validate_image_data(self, image_request: ImageUploadRequestDTO) -> None:
        """Validate base64 image data."""
        if not image_request.encoded_image:
            raise Base64ValidationError("Image data is required")
        
        # Validate base64 format
        try:
            image_data = base64.b64decode(image_request.encoded_image)
        except Exception as e:
            logger.warning(f"Invalid base64 data: {e}")
            raise Base64ValidationError("Invalid base64 image data")
        
        # Check image size
        image_size_mb = len(image_data) / (1024 * 1024)
        max_size_mb = ValidationLimits.MAX_IMAGE_SIZE_MB
        
        if image_size_mb > max_size_mb:
            raise ImageSizeError(len(image_data), max_size_mb * 1024 * 1024)
        
        # Validate image type
        image_type = imghdr.what(None, h=image_data)
        if not image_type or f"image/{image_type}" not in ValidationLimits.ALLOWED_IMAGE_TYPES:
            supported_types = [t.split('/')[-1] for t in ValidationLimits.ALLOWED_IMAGE_TYPES]
            raise UnsupportedImageTypeError(
                image_type or "unknown", 
                supported_types
            )
        
        logger.info(f"Image validation passed: type={image_type}, size={image_size_mb:.2f}MB")
    
    def _prepare_llm_request(self, image_request: ImageUploadRequestDTO) -> LLMRequestDTO:
        """Prepare request for LLM service."""
        media_data = [LLMMediaDataDTO(
            encoded_media=image_request.encoded_image,
            media_type=image_request.media_type
        )]
        
        return LLMRequestDTO(
            ai_agent_id=self.llm_config['ai_agent_id'],
            user_query="Extract the text in the image",
            configuration_environment=self.llm_config['configuration_environment'],
            media_data=media_data
        )
    
    async def _call_llm_service(self, llm_request: LLMRequestDTO) -> LLMResponseDTO:
        """Make HTTP request to LLM service."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': self.llm_config['user_agent']
        }
        
        try:
            logger.info(f"Calling LLM service: {self.llm_config['api_url']}")
            
            response = self.session.post(
                self.llm_config['api_url'],
                json=llm_request.to_dict(),
                headers=headers,
                timeout=self.llm_config['timeout']
            )
            
            logger.info(f"LLM service responded with status: {response.status_code}")
            
            if response.status_code == 408 or response.status_code == 504:
                raise LLMServiceTimeoutError(self.llm_config['timeout'])
            
            response_data = response.json() if response.content else {}
            
            if not response.ok:
                error_message = response_data.get('message', f'HTTP {response.status_code}')
                raise LLMServiceError(
                    error_message, 
                    response.status_code, 
                    response_data
                )
            
            return LLMResponseDTO.from_dict(response_data)
            
        except requests.exceptions.Timeout:
            raise LLMServiceTimeoutError(self.llm_config['timeout'])
        except requests.exceptions.ConnectionError as e:
            raise LLMServiceError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise LLMServiceError(f"Request failed: {e}")
    
    def _extract_text_from_response(self, llm_response: LLMResponseDTO) -> str:
        """Extract text content from LLM response."""
        if llm_response.error:
            error_message = llm_response.error.get('message', 'Unknown LLM error')
            raise TextExtractionError(f"LLM service error: {error_message}", llm_response.to_dict())
        
        if not llm_response.data:
            raise TextExtractionError("No data in LLM response", llm_response.to_dict())
        
        # Extract text from various possible response formats
        extracted_text = ""
        
        # Common response patterns from LLM services
        if isinstance(llm_response.data, dict):
            # Try different common field names
            text_fields = ['text', 'content', 'extracted_text', 'result', 'answer', 'response']
            
            for field in text_fields:
                if field in llm_response.data:
                    extracted_text = str(llm_response.data[field])
                    break
            
            # If no text found in common fields, try to extract from nested structures
            if not extracted_text and 'results' in llm_response.data:
                results = llm_response.data['results']
                if isinstance(results, list) and len(results) > 0:
                    first_result = results[0]
                    if isinstance(first_result, dict):
                        for field in text_fields:
                            if field in first_result:
                                extracted_text = str(first_result[field])
                                break
        
        elif isinstance(llm_response.data, str):
            extracted_text = llm_response.data
        
        if not extracted_text or extracted_text.strip() == "":
            raise TextExtractionError("No text found in image", llm_response.to_dict())
        
        logger.info(f"Successfully extracted text: {len(extracted_text)} characters")
        return extracted_text.strip()
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get LLM service health status."""
        try:
            # Simple health check - could be expanded
            return {
                "status": "healthy",
                "endpoint": self.llm_config['api_url'],
                "configuration_environment": self.llm_config['configuration_environment'],
                "timeout": self.llm_config['timeout'],
                "max_retries": self.llm_config['max_retries']
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }