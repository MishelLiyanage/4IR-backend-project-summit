"""
Validation controller implementation for handling compliance validation workflows.
"""

from typing import Dict, Any
import logging
from src.controllers import BaseController
from src.services.validation_service import ValidationService
from src.services.validation_response_formatter_service import ValidationResponseFormatterService
from src.dto import ValidationRequestDTO, ValidationResponseDTO
from src.exceptions import LLMServiceError, LLMServiceTimeoutError

logger = logging.getLogger(__name__)


class ValidationController(BaseController):
    """Controller for validation agent endpoints."""
    
    def __init__(self, validation_service: ValidationService, formatter_service: ValidationResponseFormatterService):
        """Initialize validation controller with services."""
        # Pass None as service since we're using validation service directly
        super().__init__(None)
        self._validation_service = validation_service
        self._formatter_service = formatter_service
    
    def get_routes(self) -> Dict[str, Any]:
        """Get validation controller routes configuration."""
        return {
            "POST /validation/validate-compliance": self.validate_compliance,
            "POST /validation/format-query": self.format_validation_query,
            "GET /validation/health": self.health_check,
        }
    
    async def validate_compliance(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST request for compliance validation."""
        try:
            logger.info("Processing compliance validation request")
            
            # Validate request data
            if 'validation_query' not in request_data:
                return self._bad_request_response("Missing 'validation_query' field")
            
            validation_query = request_data['validation_query']
            
            # Validate with validation service
            result = await self._validation_service.validate_compliance(validation_query)
            
            # Parse the validation response
            parsed_result = self._formatter_service.parse_validation_response(result.to_dict())
            
            logger.info("Compliance validation completed successfully")
            return self._success_response({
                "validation_result": parsed_result,
                "processing_time_ms": result.processing_time_ms,
                "raw_response": result.to_dict()
            })
            
        except LLMServiceTimeoutError as e:
            logger.error(f"Validation service timeout: {e}")
            return self._timeout_response(str(e))
        
        except LLMServiceError as e:
            logger.error(f"Validation service error: {e}")
            return self._service_error_response(str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error in validation: {e}")
            return self._internal_error_response("Failed to process validation")
    
    async def format_validation_query(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST request for formatting validation queries."""
        try:
            logger.info("Processing validation query formatting request")
            
            # Validate request data
            if 'extracted_text' not in request_data or 'rag_response' not in request_data:
                return self._bad_request_response("Missing 'extracted_text' or 'rag_response' fields")
            
            extracted_text = request_data['extracted_text']
            rag_response = request_data['rag_response']
            
            # Format validation query
            formatted_query = self._formatter_service.format_validation_query(extracted_text, rag_response)
            
            logger.info("Validation query formatting completed successfully")
            return self._success_response({
                "formatted_query": formatted_query,
                "original_extracted_text": extracted_text,
                "original_rag_response": rag_response
            })
            
        except Exception as e:
            logger.error(f"Unexpected error in query formatting: {e}")
            return self._internal_error_response("Failed to format validation query")
    
    async def process_full_validation(self, 
                                    extracted_text: str, 
                                    rag_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process complete validation workflow from extracted text and RAG response.
        This method combines formatting and validation for internal use.
        """
        try:
            logger.info("🔍 VALIDATION CONTROLLER: Processing full validation workflow")
            logger.info("📋 Step 4a/4: Formatting validation query from image extraction and RAG responses")
            
            # Format validation query
            validation_query = self._formatter_service.format_validation_query(extracted_text, rag_response)
            
            logger.info(f"✅ Step 4a/4: Validation query formatted successfully")
            logger.info("📋 Step 4b/4: Calling validation API for compliance check")
            
            # Validate compliance
            validation_result = await self._validation_service.validate_compliance(validation_query)
            
            logger.info(f"✅ Step 4b/4: Validation API response received - Processing time: {validation_result.processing_time_ms}ms")
            logger.info("📋 Step 4c/4: Parsing validation response for compliance results")
            
            # Parse the validation response
            parsed_result = self._formatter_service.parse_validation_response(validation_result.to_dict())
            
            logger.info(f"✅ Step 4c/4: Validation response parsed successfully")
            
            if parsed_result.get('success'):
                compliance_status = parsed_result['compliance']['is_compliant']
                coverage_percent = parsed_result['compliance']['coverage_percent']
                logger.info(f"📊 COMPLIANCE RESULTS: Compliant={compliance_status}, Coverage={coverage_percent}%")
            
            # Print results to terminal
            self._print_validation_results_to_terminal(validation_query, validation_result, parsed_result)
            
            logger.info("✅ Step 4c/4: Validation workflow completed successfully")
            
            return {
                "success": True,
                "validation_query": validation_query,
                "validation_result": parsed_result,
                "processing_time_ms": validation_result.processing_time_ms,
                "raw_response": validation_result.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error in full validation workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _print_validation_results_to_terminal(self, 
                                            validation_query: str, 
                                            validation_result: ValidationResponseDTO, 
                                            parsed_result: Dict[str, Any]):
        """Print validation results to terminal for debugging/monitoring."""
        print("\n" + "="*100)
        print("VALIDATION AGENT RESPONSE - COMPLIANCE CHECK")
        print("="*100)
        print(f"Processing Time: {validation_result.processing_time_ms}ms")
        print("-"*100)
        
        print("VALIDATION QUERY SENT:")
        print(validation_query)
        print("-"*100)
        
        if parsed_result.get('success'):
            compliance = parsed_result['compliance']
            issues = parsed_result['issues']
            
            print("COMPLIANCE RESULTS:")
            print(f"✅ Compliant: {compliance['is_compliant']}")
            print(f"📊 Coverage: {compliance['coverage_percent']}%")
            print(f"✓ Matched: {compliance['matched_count']}/{compliance['total_required']}")
            print(f"⚠ Partial: {compliance['partial_count']}")
            print("-"*100)
            
            if issues['missing_items']:
                print("❌ MISSING ITEMS:")
                for item in issues['missing_items']:
                    print(f"  • {item.get('key', 'N/A')}: {item.get('requirement_text', 'N/A')}")
                print("-"*50)
            
            if issues['partial_matches']:
                print("⚠ PARTIAL MATCHES:")
                for item in issues['partial_matches']:
                    print(f"  • {item.get('key', 'N/A')}: {item.get('requirement_text', 'N/A')}")
                    print(f"    Observed: {item.get('observed', 'N/A')}")
                print("-"*50)
            
            if issues['conflicts']:
                print("🚫 CONFLICTS:")
                for conflict in issues['conflicts']:
                    print(f"  • Type: {conflict.get('type', 'N/A')}")
                    print(f"    Detail: {conflict.get('detail', 'N/A')}")
                    print(f"    Observed: {conflict.get('observed', 'N/A')}")
                print("-"*50)
            
            if parsed_result.get('evidence'):
                print("📋 EVIDENCE FOUND:")
                evidence = parsed_result['evidence']
                for key, value in evidence.items():
                    if value:
                        print(f"  • {key}: {value}")
                print("-"*50)
            
            if parsed_result.get('notes'):
                print("📝 NOTES:")
                print(parsed_result['notes'])
                print("-"*50)
            
            if parsed_result.get('references'):
                print("📚 REFERENCES:")
                for ref in parsed_result['references']:
                    print(f"  • {ref}")
        else:
            print(f"❌ VALIDATION FAILED: {parsed_result.get('error', 'Unknown error')}")
        
        print("="*100 + "\n")
    
    async def health_check(self, request_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle GET request for validation service health check."""
        try:
            validation_health = self._validation_service.get_service_health()
            
            return self._success_response({
                "service": "Validation Controller",
                "validation_service": validation_health,
                "formatter_service": {"status": "healthy"},
                "status": "healthy"
            })
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return self._internal_error_response("Health check failed")