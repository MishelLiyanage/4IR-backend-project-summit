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