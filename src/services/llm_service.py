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
    
    def __init__(self, config: AppConfig, rag_controller=None):
        """Initialize LLM service with configuration and optional RAG controller."""
        self.config = config
        self.llm_config = config.get_llm_config()
        self.session = self._create_http_session()
        self.rag_controller = rag_controller
        
        logger.info(f"LLM Service initialized with endpoint: {self.llm_config['api_url']}")
        if rag_controller:
            logger.info("RAG controller integration enabled")
    
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
            logger.info("🔍 LLM SERVICE: Starting text extraction from image")
            logger.info("📋 Step 2a/4: Validating image data (size, format, encoding)")
            
            # Validate image data
            self._validate_image_data(image_request)
            
            logger.info("✅ Step 2a/4: Image validation successful")
            logger.info("📋 Step 2b/4: Preparing LLM request payload")
            
            # Prepare LLM request
            llm_request = self._prepare_llm_request(image_request)
            
            logger.info("✅ Step 2b/4: LLM request prepared")
            logger.info("📋 Step 2c/4: Calling Generic LLM API for text extraction")
            
            # Call LLM service
            llm_response = await self._call_llm_service(llm_request)
            
            logger.info("✅ Step 2c/4: Generic LLM API response received")
            logger.info("📋 Step 2d/4: Processing and extracting text from LLM response")
            
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
            
            logger.info(f"✅ Step 2d/4: Text extraction completed successfully in {processing_time}ms")
            logger.info(f"📊 Extracted text length: {len(extracted_text)} characters")
            
            # Call RAG agent if controller is available
            if self.rag_controller:
                try:
                    logger.info("📋 Step 3/4: Initiating RAG agent for regulations query")
                    rag_result = await self.rag_controller.process_extracted_text_for_regulations(extracted_text)
                    
                    if rag_result.get('success'):
                        logger.info("✅ Step 3/4: RAG agent query completed successfully")
                        
                        # Store RAG result for potential PDF generation
                        response.rag_result = rag_result
                        
                        if 'validation' in rag_result:
                            logger.info("✅ Step 4/4: Validation agent completed successfully")
                            logger.info("🎉 WORKFLOW COMPLETE: All agents processed successfully - Ready for PDF generation")
                            
                            # Extract compliance information for frontend
                            validation_data = rag_result['validation']
                            validation_result = validation_data.get('validation_result', {})
                            compliance_data = validation_result.get('compliance', {})
                            
                            response.compliance_result = {
                                "is_compliant": compliance_data.get('is_compliant', False),
                                "coverage_percent": compliance_data.get('coverage_percent', 0),
                                "validation_successful": True,
                                "ready_for_pdf": True
                            }
                            
                        elif 'validation_error' in rag_result:
                            logger.warning(f"⚠ Step 4/4: Validation agent had issues: {rag_result['validation_error']}")
                            logger.info("🎯 WORKFLOW PARTIAL: RAG successful, validation had issues")
                            response.compliance_result = {
                                "validation_successful": False,
                                "error": rag_result['validation_error'],
                                "ready_for_pdf": False
                            }
                    else:
                        logger.warning(f"❌ Step 3/4: RAG agent query failed: {rag_result.get('error')}")
                        logger.info("⚠ WORKFLOW PARTIAL: Text extraction successful, RAG failed")
                        response.compliance_result = {
                            "rag_successful": False,
                            "error": rag_result.get('error'),
                            "frontend_message": rag_result.get('frontend_message'),
                            "ready_for_pdf": False
                        }
                        
                except Exception as rag_error:
                    logger.error(f"💥 RAG agent integration error: {rag_error}")
                    logger.info("⚠ WORKFLOW PARTIAL: Text extraction successful, RAG integration failed")
                    response.compliance_result = {
                        "rag_successful": False, 
                        "error": str(rag_error),
                        "ready_for_pdf": False
                    }
                    # Don't fail the main process if RAG fails
            else:
                logger.info("ℹ RAG controller not available - completing with text extraction only")
            
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
        
        extracted_text = ""
        
        # Common response patterns
        if isinstance(llm_response.data, dict):
            text_fields = ['text', 'content', 'extracted_text', 'result', 'answer', 'response']
            
            # Direct text fields
            for field in text_fields:
                if field in llm_response.data:
                    extracted_text = str(llm_response.data[field])
                    break
            
            # Nested "results"
            if not extracted_text and 'results' in llm_response.data:
                results = llm_response.data['results']
                if isinstance(results, list) and results:
                    first_result = results[0]
                    if isinstance(first_result, dict):
                        for field in text_fields:
                            if field in first_result:
                                extracted_text = str(first_result[field])
                                break
            
            # Handle "responses -> agent_response"
            if not extracted_text and 'responses' in llm_response.data:
                responses = llm_response.data['responses']
                if isinstance(responses, dict) and 'agent_response' in responses:
                    agent_resp = responses['agent_response']
                    if isinstance(agent_resp, dict):
                        # Collect values of all fields into a readable string
                        extracted_parts = []
                        for key, value in agent_resp.items():
                            extracted_parts.append(f"{key.replace('_', ' ').title()}: {value}")
                        extracted_text = "\n".join(extracted_parts)
        
        elif isinstance(llm_response.data, str):
            extracted_text = llm_response.data
        
        if not extracted_text or extracted_text.strip() == "":
            raise TextExtractionError("No text found in LLM response", llm_response.to_dict())
        
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