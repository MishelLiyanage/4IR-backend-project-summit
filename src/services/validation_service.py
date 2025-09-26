"""
Validation service for communicating with the Generic LLM Platform for validation.
"""

import logging
import time
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.constants import AppConfig
from src.exceptions import LLMServiceError, LLMServiceTimeoutError
from src.dto import ValidationRequestDTO, ValidationResponseDTO

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validation agent communication using Generic LLM Platform."""
    
    def __init__(self, config: AppConfig):
        """Initialize validation service with configuration."""
        self.config = config
        self.validation_config = self._get_validation_config()
        self.session = self._create_http_session()
        
        logger.info(f"Validation Service initialized with endpoint: {self.validation_config['api_url']}")
    
    def _get_validation_config(self) -> Dict[str, Any]:
        """Get validation service configuration."""
        return {
            'api_url': 'https://sage.paastry.sysco.net/api/sysco-gen-ai-platform/agents/v1/content/generic/answer',
            'ai_agent_id': '68d5871022a20d9ed21b026e',
            'configuration_environment': 'DEV',
            'timeout': 60,  # Validation might take longer
            'max_retries': 3,
            'user_agent': 'insomnium/1.3.0'
        }
    
    def _create_http_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.validation_config['max_retries'],
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    async def validate_compliance(self, validation_query: str) -> ValidationResponseDTO:
        """
        Validate compliance by sending combined image extraction and RAG responses.
        
        Args:
            validation_query: JSON string containing image_extraction_raw and rag_raw
            
        Returns:
            ValidationResponseDTO with compliance results
        """
        start_time = time.time()
        
        try:
            logger.info("Starting validation compliance check")
            
            # Prepare validation request
            validation_request = ValidationRequestDTO(
                ai_agent_id=self.validation_config['ai_agent_id'],
                user_query=validation_query,
                configuration_environment=self.validation_config['configuration_environment']
            )
            
            # Call validation service
            validation_response = await self._call_validation_service(validation_request)
            
            processing_time = int((time.time() - start_time) * 1000)
            validation_response.processing_time_ms = processing_time
            
            logger.info(f"Validation compliance check completed in {processing_time}ms")
            return validation_response
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Validation compliance check failed after {processing_time}ms: {e}")
            raise
    
    async def _call_validation_service(self, validation_request: ValidationRequestDTO) -> ValidationResponseDTO:
        """Make HTTP request to validation service."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': self.validation_config['user_agent']
        }
        
        try:
            logger.info(f"Calling validation service: {self.validation_config['api_url']}")
            
            response = self.session.post(
                self.validation_config['api_url'],
                json=validation_request.to_dict(),
                headers=headers,
                timeout=self.validation_config['timeout']
            )
            
            logger.info(f"Validation service responded with status: {response.status_code}")
            
            if response.status_code == 408 or response.status_code == 504:
                raise LLMServiceTimeoutError(self.validation_config['timeout'])
            
            response_data = response.json() if response.content else {}
            
            if not response.ok:
                error_message = response_data.get('message', f'HTTP {response.status_code}')
                raise LLMServiceError(
                    error_message, 
                    response.status_code, 
                    response_data
                )
            
            return ValidationResponseDTO.from_dict(response_data)
            
        except requests.exceptions.Timeout:
            raise LLMServiceTimeoutError(self.validation_config['timeout'])
        except requests.exceptions.ConnectionError as e:
            raise LLMServiceError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise LLMServiceError(f"Request failed: {e}")
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get validation service health status."""
        try:
            return {
                "status": "healthy",
                "endpoint": self.validation_config['api_url'],
                "ai_agent_id": self.validation_config['ai_agent_id'],
                "configuration_environment": self.validation_config['configuration_environment'],
                "timeout": self.validation_config['timeout'],
                "max_retries": self.validation_config['max_retries']
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }