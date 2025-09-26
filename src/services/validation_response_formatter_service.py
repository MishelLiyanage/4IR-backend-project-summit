"""
Response formatter service for structuring image extraction and RAG responses for validation.
"""

import logging
import json
import re
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ValidationResponseFormatterService:
    """Service for formatting responses for validation agent."""
    
    def __init__(self):
        """Initialize validation response formatter service."""
        logger.info("Validation Response Formatter Service initialized")
    
    def format_validation_query(self, 
                               extracted_text: str, 
                               rag_response: Dict[str, Any]) -> str:
        """
        Format image extraction and RAG responses into validation query structure.
        
        Args:
            extracted_text: Raw text extracted from image by LLM
            rag_response: Response from RAG agent containing regulations
            
        Returns:
            JSON string formatted for validation agent
        """
        try:
            logger.info("Formatting validation query from image extraction and RAG responses")
            
            # Format image extraction response
            image_extraction_formatted = self._format_image_extraction_response(extracted_text)
            
            # Format RAG response
            rag_formatted = self._format_rag_response(rag_response)
            
            # Combine into validation query structure
            validation_query = {
                "image_extraction_raw": image_extraction_formatted,
                "rag_raw": rag_formatted
            }
            
            # Convert to JSON string
            validation_query_json = json.dumps(validation_query, ensure_ascii=False, separators=(',', ':'))
            
            logger.info("Validation query formatted successfully")
            return validation_query_json
            
        except Exception as e:
            logger.error(f"Error formatting validation query: {e}")
            raise
    
    def _format_image_extraction_response(self, extracted_text: str) -> Dict[str, Any]:
        """Format image extraction text into structured response."""
        try:
            # Extract structured information from the raw text
            product_info = self._extract_product_information(extracted_text)
            
            return {
                "agent_response": {
                    "product_name": product_info.get("product_name", ""),
                    "export_country_or_state": product_info.get("export_country_or_state", ""),
                    "supplementary_details": product_info.get("supplementary_details", extracted_text.strip())
                }
            }
            
        except Exception as e:
            logger.error(f"Error formatting image extraction response: {e}")
            # Fallback to basic structure
            return {
                "agent_response": {
                    "product_name": "",
                    "export_country_or_state": "",
                    "supplementary_details": extracted_text.strip()
                }
            }
    
    def _format_rag_response(self, rag_response: Dict[str, Any]) -> Dict[str, Any]:
        """Format RAG response into validation structure."""
        try:
            # Extract answer and sources from RAG response
            agent_response = ""
            references = []
            
            if isinstance(rag_response, dict):
                # Try to get the answer/regulations text
                agent_response = (
                    rag_response.get("answer", "") or 
                    rag_response.get("regulations", "") or 
                    rag_response.get("response", "") or
                    str(rag_response.get("data", ""))
                )
                
                # Try to get sources/references
                sources = rag_response.get("sources", []) or rag_response.get("references", [])
                if sources:
                    references = sources if isinstance(sources, list) else [str(sources)]
                else:
                    # Default reference if none provided
                    references = ["Regulatory_Database.pdf"]
            
            return {
                "agent_response": agent_response.strip() if agent_response else "No regulations found",
                "references": references
            }
            
        except Exception as e:
            logger.error(f"Error formatting RAG response: {e}")
            # Fallback structure
            return {
                "agent_response": "Error processing regulatory information",
                "references": ["Error_Processing.pdf"]
            }
    
    def _extract_product_information(self, text: str) -> Dict[str, str]:
        """Extract structured product information from raw text."""
        info = {
            "product_name": "",
            "export_country_or_state": "",
            "supplementary_details": text.strip()
        }
        
        try:
            # Extract product name
            product_patterns = [
                r'Product\s*(?:Name)?:\s*([^\n\r]+)',
                r'Product:\s*([^\n\r]+)',
                r'Name:\s*([^\n\r]+)',
            ]
            
            for pattern in product_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info["product_name"] = match.group(1).strip()
                    break
            
            # Extract country/state information
            country_patterns = [
                r'Destination\s*(?:Country)?:\s*([^\n\r]+)',
                r'Export\s*(?:to|Country):\s*([^\n\r]+)',
                r'Country:\s*([^\n\r]+)',
                r'(?:Dubai|UAE|United Arab Emirates|Canada|USA|United States)',
            ]
            
            for pattern in country_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if len(pattern.split('|')) > 1:  # Pattern with alternatives
                        info["export_country_or_state"] = match.group(0).strip()
                    else:
                        info["export_country_or_state"] = match.group(1).strip()
                    break
            
            # Extract additional details like ingredients, claims, etc.
            detail_patterns = [
                r'Ingredients?:\s*([^\n\r]+(?:\n\s*[-•]\s*[^\n\r]+)*)',
                r'Claims?:\s*([^\n\r]+)',
                r'Net\s*(?:Weight|Quantity)?:\s*([^\n\r]+)',
                r'Manufacturer:\s*([^\n\r]+)',
                r'Certification:\s*([^\n\r]+)',
            ]
            
            additional_details = []
            for pattern in detail_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    detail = match.group(0).strip()
                    if detail and detail not in additional_details:
                        additional_details.append(detail)
            
            if additional_details:
                info["supplementary_details"] = ". ".join(additional_details)
            
        except Exception as e:
            logger.warning(f"Error extracting product information: {e}")
        
        return info
    
    def parse_validation_response(self, validation_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and structure the validation response for better readability.
        
        Args:
            validation_response: Raw response from validation agent
            
        Returns:
            Structured validation results
        """
        try:
            logger.info("Parsing validation response")
            
            if not validation_response or validation_response.get("status") != "success":
                return {
                    "success": False,
                    "error": "Validation failed or returned error status"
                }
            
            answer = validation_response.get("answer", {})
            agent_response = answer.get("agent_response", {})
            
            parsed_result = {
                "success": True,
                "compliance": {
                    "is_compliant": agent_response.get("compliance", "false").lower() == "true",
                    "coverage_percent": agent_response.get("coverage_percent", 0),
                    "matched_count": agent_response.get("matched_count", 0),
                    "partial_count": agent_response.get("partial_count", 0),
                    "total_required": agent_response.get("total_required", 0)
                },
                "issues": {
                    "missing_items": agent_response.get("missing_items", []),
                    "partial_matches": agent_response.get("partial_matches", []),
                    "conflicts": agent_response.get("conflicts", [])
                },
                "evidence": agent_response.get("evidence", {}),
                "notes": agent_response.get("notes", ""),
                "references": answer.get("references", [])
            }
            
            logger.info(f"Validation response parsed successfully - Compliance: {parsed_result['compliance']['is_compliant']}")
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error parsing validation response: {e}")
            return {
                "success": False,
                "error": f"Failed to parse validation response: {str(e)}"
            }