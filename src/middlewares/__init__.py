"""
Middleware components for cross-cutting concerns.
"""

import logging
import time
from typing import Any, Dict, Callable, Optional
from datetime import datetime
from src.constants import HttpStatus
from src.exceptions import BaseApplicationException
from src.dto import ErrorResponseDTO

logger = logging.getLogger(__name__)


class BaseMiddleware:
    """Base middleware class."""
    
    def __init__(self, name: str):
        """Initialize middleware."""
        self.name = name
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming request. Override in subclasses."""
        return request_data
    
    async def process_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process outgoing response. Override in subclasses."""
        return response_data
    
    async def process_exception(self, exception: Exception) -> Optional[Dict[str, Any]]:
        """Process exceptions. Override in subclasses."""
        return None


class LoggingMiddleware(BaseMiddleware):
    """Middleware for request/response logging."""
    
    def __init__(self):
        """Initialize logging middleware."""
        super().__init__("LoggingMiddleware")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log incoming request."""
        logger.info(f"Incoming request: {request_data.get('method', 'UNKNOWN')} {request_data.get('path', '/')}")
        
        # Use sanitized body for logging if available (for image requests)
        log_data = request_data.copy()
        if '_sanitized_body' in request_data:
            log_data['body'] = request_data['_sanitized_body']
        
        logger.debug(f"Request data: {log_data}")
        
        # Add timestamp to request
        request_data['_start_time'] = time.time()
        request_data['_request_id'] = f"req_{int(time.time() * 1000)}"
        
        return request_data
    
    async def process_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log outgoing response."""
        status_code = response_data.get('status_code', 200)
        
        # Calculate response time if start time is available
        start_time = response_data.get('_start_time')
        response_time = f" ({(time.time() - start_time) * 1000:.2f}ms)" if start_time else ""
        
        logger.info(f"Response: {status_code}{response_time}")
        
        if status_code >= 400:
            logger.warning(f"Error response: {response_data}")
        else:
            logger.debug(f"Response data: {response_data}")
        
        return response_data


class ExceptionHandlingMiddleware(BaseMiddleware):
    """Middleware for centralized exception handling."""
    
    def __init__(self):
        """Initialize exception handling middleware."""
        super().__init__("ExceptionHandlingMiddleware")
    
    async def process_exception(self, exception: Exception) -> Dict[str, Any]:
        """Handle and format exceptions."""
        logger.exception(f"Unhandled exception: {exception}")
        
        # Handle custom application exceptions
        if isinstance(exception, BaseApplicationException):
            error_dto = ErrorResponseDTO.from_exception(exception)
            status_code = self._get_status_code_for_exception(exception)
            
            return {
                "status": "error",
                "status_code": status_code,
                "error": error_dto.to_dict()
            }
        
        # Handle standard Python exceptions
        error_dto = ErrorResponseDTO.from_exception(exception)
        
        return {
            "status": "error",
            "status_code": HttpStatus.INTERNAL_SERVER_ERROR,
            "error": error_dto.to_dict()
        }
    
    def _get_status_code_for_exception(self, exception: BaseApplicationException) -> int:
        """Map exception types to HTTP status codes."""
        from src.exceptions import (
            ValidationException, NotFoundError, ConflictError,
            AuthenticationError, AuthorizationError, BusinessRuleViolationError
        )
        
        exception_status_map = {
            ValidationException: HttpStatus.BAD_REQUEST,
            NotFoundError: HttpStatus.NOT_FOUND,
            ConflictError: HttpStatus.CONFLICT,
            AuthenticationError: HttpStatus.UNAUTHORIZED,
            AuthorizationError: HttpStatus.FORBIDDEN,
            BusinessRuleViolationError: HttpStatus.BAD_REQUEST,
        }
        
        return exception_status_map.get(type(exception), HttpStatus.INTERNAL_SERVER_ERROR)


class ValidationMiddleware(BaseMiddleware):
    """Middleware for request validation."""
    
    def __init__(self):
        """Initialize validation middleware."""
        super().__init__("ValidationMiddleware")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate incoming request."""
        # Basic request validation
        if not isinstance(request_data, dict):
            raise ValueError("Invalid request format")
        
        # Special handling for image processing requests
        if self._is_image_processing_request(request_data):
            self._validate_image_request(request_data)
        
        # Add validation timestamp
        request_data['_validated_at'] = datetime.utcnow().isoformat()
        
        return request_data
    
    def _is_image_processing_request(self, request_data: Dict[str, Any]) -> bool:
        """Check if this is an image processing request."""
        path = request_data.get('path', '')
        return '/images/' in path or 'encoded_image' in request_data.get('body', {})
    
    def _validate_image_request(self, request_data: Dict[str, Any]) -> None:
        """Validate image processing specific requests."""
        body = request_data.get('body', {})
        
        # Log image request (without the actual image data for security)
        logger.info(f"Validating image processing request: {request_data.get('method')} {request_data.get('path')}")
        
        if 'encoded_image' in body:
            encoded_image = body['encoded_image']
            
            # Basic size check for base64 data
            if len(encoded_image) > 10 * 1024 * 1024:  # 10MB limit for base64
                raise ValueError("Image data too large")
            
            # Log image size info
            image_size_kb = len(encoded_image) / 1024
            logger.info(f"Image request - Base64 size: {image_size_kb:.1f} KB")
            
            # Don't log the actual image data
            body_copy = body.copy()
            body_copy['encoded_image'] = f"<base64_data_{len(encoded_image)}_bytes>"
            request_data['_sanitized_body'] = body_copy


class SecurityMiddleware(BaseMiddleware):
    """Middleware for security headers and basic security checks."""
    
    def __init__(self):
        """Initialize security middleware."""
        super().__init__("SecurityMiddleware")
    
    async def process_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add security headers to response."""
        if 'headers' not in response_data:
            response_data['headers'] = {}
        
        # Add security headers
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        response_data['headers'].update(security_headers)
        return response_data


class PerformanceMiddleware(BaseMiddleware):
    """Middleware for performance monitoring."""
    
    def __init__(self):
        """Initialize performance middleware."""
        super().__init__("PerformanceMiddleware")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start performance tracking."""
        request_data['_perf_start'] = time.perf_counter()
        return request_data
    
    async def process_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add performance metrics to response."""
        start_time = response_data.get('_perf_start')
        if start_time:
            duration = time.perf_counter() - start_time
            response_data['_performance'] = {
                'duration_ms': round(duration * 1000, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Log slow requests
            if duration > 1.0:  # Slower than 1 second
                logger.warning(f"Slow request detected: {duration * 1000:.2f}ms")
        
        return response_data


class MiddlewareChain:
    """Chain of middleware components."""
    
    def __init__(self):
        """Initialize middleware chain."""
        self.middlewares = []
    
    def add_middleware(self, middleware: BaseMiddleware):
        """Add middleware to the chain."""
        self.middlewares.append(middleware)
        logger.info(f"Added middleware: {middleware.name}")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process request through all middlewares."""
        current_data = request_data.copy()
        
        for middleware in self.middlewares:
            try:
                current_data = await middleware.process_request(current_data)
            except Exception as e:
                logger.error(f"Error in middleware {middleware.name}: {e}")
                raise
        
        return current_data
    
    async def process_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process response through all middlewares (in reverse order)."""
        current_data = response_data.copy()
        
        # Process middlewares in reverse order for response
        for middleware in reversed(self.middlewares):
            try:
                current_data = await middleware.process_response(current_data)
            except Exception as e:
                logger.error(f"Error in middleware {middleware.name}: {e}")
                # Continue processing other middlewares for responses
        
        return current_data
    
    async def process_exception(self, exception: Exception) -> Optional[Dict[str, Any]]:
        """Process exception through middlewares."""
        for middleware in self.middlewares:
            try:
                result = await middleware.process_exception(exception)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Error in exception handling middleware {middleware.name}: {e}")
        
        return None