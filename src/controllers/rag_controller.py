"""
RAG controller implementation for handling rules and regulations queries.
"""

from typing import Dict, Any
import logging
from src.controllers import BaseController
from src.services.rag_service import RAGService
from src.services.query_formatter_service import QueryFormatterService
from src.dto import RAGRequestDTO, RAGResponseDTO
from src.exceptions import LLMServiceError, LLMServiceTimeoutError

logger = logging.getLogger(__name__)


class RAGController(BaseController):
    """Controller for RAG agent endpoints."""
    
    def __init__(self, rag_service: RAGService, query_formatter_service: QueryFormatterService, validation_controller=None):
        """Initialize RAG controller with services and optional validation controller."""
        # Pass None as service since we're using RAG service directly
        super().__init__(None)
        self._rag_service = rag_service
        self._query_formatter_service = query_formatter_service
        self.validation_controller = validation_controller
        
        if validation_controller:
            logger.info("Validation controller integrated with RAG controller")
    
    def get_routes(self) -> Dict[str, Any]:
        """Get RAG controller routes configuration."""
        return {
            "POST /rag/query-regulations": self.query_regulations,
            "POST /rag/format-query": self.format_query,
            "GET /rag/health": self.health_check,
        }
    
    async def query_regulations(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST request for querying regulations via RAG agent."""
        try:
            logger.info("Processing RAG regulations query request")
            
            # Validate request data
            if 'user_query' not in request_data:
                return self._bad_request_response("Missing 'user_query' field")
            
            user_query = request_data['user_query']
            
            # Query RAG service
            result = await self._rag_service.query_regulations(user_query)
            
            logger.info("RAG query completed successfully")
            return self._success_response({
                "regulations": result.answer,
                "sources": result.sources,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms,
                "query": user_query
            })
            
        except LLMServiceTimeoutError as e:
            logger.error(f"RAG service timeout: {e}")
            return self._timeout_response(str(e))
        
        except LLMServiceError as e:
            logger.error(f"RAG service error: {e}")
            return self._service_error_response(str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error in RAG query: {e}")
            return self._internal_error_response("Failed to process RAG query")
    
    async def format_query(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST request for formatting RAG queries from extracted text."""
        try:
            logger.info("Processing query formatting request")
            
            # Validate request data
            if 'extracted_text' not in request_data:
                return self._bad_request_response("Missing 'extracted_text' field")
            
            extracted_text = request_data['extracted_text']
            
            # Extract regulation information
            regulation_info = self._query_formatter_service.extract_regulation_info(extracted_text)
            
            # Format RAG query
            formatted_query = self._query_formatter_service.format_rag_query(regulation_info)
            
            logger.info("Query formatting completed successfully")
            return self._success_response({
                "formatted_query": formatted_query,
                "extracted_info": regulation_info,
                "original_text": extracted_text
            })
            
        except Exception as e:
            logger.error(f"Unexpected error in query formatting: {e}")
            return self._internal_error_response("Failed to format query")
    
    async def process_extracted_text_for_regulations(self, extracted_text: str) -> Dict[str, Any]:
        """
        Process extracted text and query regulations.
        This method combines formatting and querying for internal use.
        """
        try:
            logger.info("🔍 RAG CONTROLLER: Processing extracted text for regulations")
            logger.info("📋 Step 3a/4: Extracting regulation information from text")
            
            # Extract regulation information
            regulation_info = self._query_formatter_service.extract_regulation_info(extracted_text)
            
            logger.info(f"✅ Step 3a/4: Regulation info extracted - Countries: {len(regulation_info.get('countries', []))}, Ingredients: {len(regulation_info.get('ingredients', []))}")
            logger.info("📋 Step 3b/4: Formatting RAG query for regulations API")
            
            # Format RAG query
            formatted_query = self._query_formatter_service.format_rag_query(regulation_info)
            
            logger.info(f"✅ Step 3b/4: RAG query formatted - Query: {formatted_query}")
            logger.info("📋 Step 3c/4: Calling RAG API for regulations")
            
            # Query RAG service
            rag_result = await self._rag_service.query_regulations(formatted_query)
            
            logger.info(f"✅ Step 3c/4: RAG API response received - Processing time: {rag_result.processing_time_ms}ms")
            
            # Print results to terminal
            self._print_rag_results_to_terminal(formatted_query, rag_result, regulation_info)
            
            result = {
                "success": True,
                "query": formatted_query,
                "regulations": rag_result.answer,
                "sources": rag_result.sources,
                "confidence": rag_result.confidence,
                "processing_time_ms": rag_result.processing_time_ms,
                "extracted_info": regulation_info
            }
            
            # Check if RAG result answer is None before proceeding with validation
            if rag_result.answer is None or (isinstance(rag_result.answer, str) and rag_result.answer.strip() == ""):
                logger.warning("❌ Step 3c/4: RAG service returned no regulations - skipping validation")
                logger.info("⚠ WORKFLOW PARTIAL: Text extraction successful, but no regulations found")
                result["success"] = False
                result["error"] = "No regulations found for the specified product and destination. Please verify the product details and destination country/state."
                result["frontend_message"] = "Unable to find regulations for this product and destination. Please check the product information and try again."
                return result
            
            logger.info("✅ Step 3c/4: RAG service returned valid regulations")
            
            # Call validation controller if available and RAG result has valid answer
            if self.validation_controller:
                try:
                    logger.info("📋 Step 4/4: Initiating validation agent for compliance check")
                    rag_response_dict = {
                        "answer": rag_result.answer,
                        "sources": rag_result.sources,
                        "confidence": rag_result.confidence
                    }
                    
                    validation_result = await self.validation_controller.process_full_validation(
                        extracted_text, rag_response_dict
                    )
                    
                    if validation_result.get('success'):
                        logger.info("✅ Step 4/4: Validation agent check completed successfully")
                        logger.info("🎉 WORKFLOW COMPLETE: All steps completed successfully - Ready for PDF generation")
                        result["validation"] = validation_result
                    else:
                        logger.warning(f"❌ Step 4/4: Validation agent check failed: {validation_result.get('error')}")
                        logger.info("⚠ WORKFLOW PARTIAL: RAG successful, validation failed")
                        result["validation_error"] = validation_result.get('error')
                        
                except Exception as validation_error:
                    logger.error(f"💥 Step 4/4: Validation agent integration error: {validation_error}")
                    logger.info("⚠ WORKFLOW PARTIAL: RAG successful, validation integration failed")
                    result["validation_error"] = str(validation_error)
                    # Don't fail the main process if validation fails
            else:
                logger.info("ℹ Validation controller not available - completing with RAG results only")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing extracted text for regulations: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _print_rag_results_to_terminal(self, query: str, rag_result: RAGResponseDTO, regulation_info: Dict[str, Any]):
        """Print RAG results to terminal for debugging/monitoring."""
        print("\n" + "="*80)
        print("RAG AGENT RESPONSE - RULES & REGULATIONS")
        print("="*80)
        print(f"Query: {query}")
        print(f"Processing Time: {rag_result.processing_time_ms}ms")
        print("-"*80)
        
        print("EXTRACTED INFORMATION:")
        print(f"Countries: {regulation_info.get('countries', [])}")
        print(f"States: {regulation_info.get('states', [])}")
        print(f"Ingredients: {regulation_info.get('ingredients', [])}")
        print(f"Products: {regulation_info.get('products', [])}")
        print("-"*80)
        
        print("REGULATIONS RESPONSE:")
        if rag_result.answer:
            print(rag_result.answer)
        else:
            print("No regulations found or response was empty")
        
        if rag_result.sources:
            print("\nSOURCES:")
            for i, source in enumerate(rag_result.sources, 1):
                print(f"{i}. {source}")
        
        print(f"\nConfidence: {rag_result.confidence if rag_result.confidence else 'N/A'}")
        print("="*80 + "\n")
    
    async def health_check(self, request_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle GET request for RAG service health check."""
        try:
            rag_health = self._rag_service.get_service_health()
            
            return self._success_response({
                "service": "RAG Controller",
                "rag_service": rag_health,
                "status": "healthy"
            })
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return self._internal_error_response("Health check failed")