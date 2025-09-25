"""
Custom exception classes for the application.
"""

from typing import Any, Dict, Optional


class BaseApplicationException(Exception):
    """Base exception class for all application exceptions."""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Initialize base exception."""
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "message": self.message,
            "code": self.code,
            "type": self.__class__.__name__,
            "details": self.details
        }


class ValidationException(BaseApplicationException):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        """Initialize validation exception."""
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field
        self.value = value


class NotFoundError(BaseApplicationException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource_type: str, identifier: str):
        """Initialize not found exception."""
        message = f"{resource_type} not found: {identifier}"
        details = {
            "resource_type": resource_type,
            "identifier": identifier
        }
        super().__init__(message, "NOT_FOUND", details)
        self.resource_type = resource_type
        self.identifier = identifier


class ConflictError(BaseApplicationException):
    """Exception raised when there's a conflict with existing data."""
    
    def __init__(self, message: str, conflicting_field: Optional[str] = None, conflicting_value: Any = None):
        """Initialize conflict exception."""
        details = {}
        if conflicting_field:
            details["conflicting_field"] = conflicting_field
        if conflicting_value is not None:
            details["conflicting_value"] = str(conflicting_value)
        
        super().__init__(message, "CONFLICT", details)
        self.conflicting_field = conflicting_field
        self.conflicting_value = conflicting_value


class BusinessRuleViolationError(BaseApplicationException):
    """Exception raised when business rules are violated."""
    
    def __init__(self, rule_name: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Initialize business rule violation exception."""
        details = {"rule_name": rule_name}
        if context:
            details.update(context)
        
        super().__init__(message, "BUSINESS_RULE_VIOLATION", details)
        self.rule_name = rule_name
        self.context = context or {}


class AuthenticationError(BaseApplicationException):
    """Exception raised for authentication failures."""
    
    def __init__(self, message: str = "Authentication failed"):
        """Initialize authentication exception."""
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(BaseApplicationException):
    """Exception raised for authorization failures."""
    
    def __init__(self, message: str = "Insufficient permissions", required_permission: Optional[str] = None):
        """Initialize authorization exception."""
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        
        super().__init__(message, "AUTHORIZATION_ERROR", details)
        self.required_permission = required_permission


class DatabaseError(BaseApplicationException):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None, table: Optional[str] = None):
        """Initialize database exception."""
        details = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        
        super().__init__(message, "DATABASE_ERROR", details)
        self.operation = operation
        self.table = table


class ExternalServiceError(BaseApplicationException):
    """Exception raised for external service failures."""
    
    def __init__(self, service_name: str, message: str, status_code: Optional[int] = None):
        """Initialize external service exception."""
        details = {"service_name": service_name}
        if status_code:
            details["status_code"] = status_code
        
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)
        self.service_name = service_name
        self.status_code = status_code


class ConfigurationError(BaseApplicationException):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, parameter: str, message: Optional[str] = None):
        """Initialize configuration exception."""
        message = message or f"Invalid configuration for parameter: {parameter}"
        details = {"parameter": parameter}
        
        super().__init__(message, "CONFIGURATION_ERROR", details)
        self.parameter = parameter


class ImageProcessingError(BaseApplicationException):
    """Exception raised for image processing failures."""
    
    def __init__(self, message: str, image_type: Optional[str] = None, image_size: Optional[int] = None):
        """Initialize image processing exception."""
        details = {}
        if image_type:
            details["image_type"] = image_type
        if image_size:
            details["image_size_bytes"] = image_size
        
        super().__init__(message, "IMAGE_PROCESSING_ERROR", details)
        self.image_type = image_type
        self.image_size = image_size


class Base64ValidationError(ValidationException):
    """Exception raised for base64 validation failures."""
    
    def __init__(self, message: str = "Invalid base64 data"):
        """Initialize base64 validation exception."""
        super().__init__(message, "base64_data")


class ImageSizeError(ImageProcessingError):
    """Exception raised when image size exceeds limits."""
    
    def __init__(self, actual_size: int, max_size: int):
        """Initialize image size exception."""
        message = f"Image size {actual_size} bytes exceeds maximum allowed size {max_size} bytes"
        super().__init__(message, image_size=actual_size)
        self.actual_size = actual_size
        self.max_size = max_size


class UnsupportedImageTypeError(ImageProcessingError):
    """Exception raised for unsupported image types."""
    
    def __init__(self, image_type: str, supported_types: list):
        """Initialize unsupported image type exception."""
        message = f"Unsupported image type: {image_type}. Supported types: {', '.join(supported_types)}"
        super().__init__(message, image_type=image_type)
        self.supported_types = supported_types


class LLMServiceError(ExternalServiceError):
    """Exception raised for LLM service failures."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        """Initialize LLM service exception."""
        super().__init__("LLM Service", message, status_code)
        if response_data:
            self.details.update({"response_data": response_data})
        self.response_data = response_data


class LLMServiceTimeoutError(LLMServiceError):
    """Exception raised when LLM service request times out."""
    
    def __init__(self, timeout_seconds: int):
        """Initialize LLM service timeout exception."""
        message = f"LLM service request timed out after {timeout_seconds} seconds"
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class TextExtractionError(BaseApplicationException):
    """Exception raised when text extraction fails."""
    
    def __init__(self, message: str = "Failed to extract text from image", llm_response: Optional[Dict[str, Any]] = None):
        """Initialize text extraction exception."""
        details = {}
        if llm_response:
            details["llm_response"] = llm_response
        
        super().__init__(message, "TEXT_EXTRACTION_ERROR", details)
        self.llm_response = llm_response