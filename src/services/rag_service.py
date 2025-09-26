"""
RAG service for querying rules and regulations from Sysco Gen AI Platform.
"""

import logging
import time
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.constants import AppConfig
from src.exceptions import LLMServiceError, LLMServiceTimeoutError
from src.dto import RAGRequestDTO, RAGResponseDTO

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG agent communication to fetch rules and regulations."""
    
    def __init__(self, config: AppConfig):
        """Initialize RAG service with configuration."""
        self.config = config
        self.rag_config = self._get_rag_config()
        self.session = self._create_http_session()
        
        logger.info(f"RAG Service initialized with endpoint: {self.rag_config['api_url']}")
    
    def _get_rag_config(self) -> Dict[str, Any]:
        """Get RAG service configuration."""
        return {
            'api_url': 'https://sage.paastry.sysco.net/api/sysco-gen-ai-platform/agents/v1/content/rag/answer',
            'ai_agent_id': '67c6dc7038969effe4737229',
            'configuration_environment': 'DEV',
            'timeout': 30,
            'max_retries': 3,
            'user_agent': 'insomnium/1.3.0'
        }
    
    def _create_http_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.rag_config['max_retries'],
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    async def query_regulations(self, user_query: str) -> RAGResponseDTO:
        """Query RAG agent for rules and regulations."""
        start_time = time.time()
        
        try:
            logger.info(f"Starting RAG query: {user_query}")
            
            # Prepare RAG request
            rag_request = RAGRequestDTO(
                ai_agent_id=self.rag_config['ai_agent_id'],
                user_query=user_query,
                configuration_environment=self.rag_config['configuration_environment']
            )
            
            # Call RAG service
            rag_response = await self._call_rag_service(rag_request)
            
            processing_time = int((time.time() - start_time) * 1000)
            rag_response.processing_time_ms = processing_time
            
            logger.info(f"RAG query completed in {processing_time}ms")
            return rag_response
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"RAG query failed after {processing_time}ms: {e}")
            raise
    
    async def _call_rag_service(self, rag_request: RAGRequestDTO) -> RAGResponseDTO:
        """Make HTTP request to RAG service."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': self.rag_config['user_agent']
        }
        
        try:
            logger.info(f"Calling RAG service: {self.rag_config['api_url']}")
            
            response = self.session.post(
                self.rag_config['api_url'],
                json=rag_request.to_dict(),
                headers=headers,
                timeout=self.rag_config['timeout']
            )
            
            logger.info(f"RAG service responded with status: {response.status_code}")
            
            if response.status_code == 408 or response.status_code == 504:
                raise LLMServiceTimeoutError(self.rag_config['timeout'])
            
            response_data = response.json() if response.content else {}
            
            if not response.ok:
                error_message = response_data.get('message', f'HTTP {response.status_code}')
                raise LLMServiceError(
                    error_message, 
                    response.status_code, 
                    response_data
                )
            
            return RAGResponseDTO.from_dict(response_data)
            
        except requests.exceptions.Timeout:
            raise LLMServiceTimeoutError(self.rag_config['timeout'])
        except requests.exceptions.ConnectionError as e:
            raise LLMServiceError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise LLMServiceError(f"Request failed: {e}")
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get RAG service health status."""
        try:
            return {
                "status": "healthy",
                "endpoint": self.rag_config['api_url'],
                "ai_agent_id": self.rag_config['ai_agent_id'],
                "configuration_environment": self.rag_config['configuration_environment'],
                "timeout": self.rag_config['timeout'],
                "max_retries": self.rag_config['max_retries']
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }