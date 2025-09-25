"""
Application constants and configuration values.
"""

import os
from enum import Enum
from typing import Dict, Any


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class UserStatus(Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class HttpStatus:
    """HTTP status codes."""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500


class DatabaseTables:
    """Database table names."""
    USERS = "users"
    SESSIONS = "sessions"
    AUDIT_LOGS = "audit_logs"


class CacheKeys:
    """Cache key templates."""
    USER_BY_ID = "user:id:{user_id}"
    USER_BY_EMAIL = "user:email:{email}"
    ACTIVE_USERS = "users:active"
    USER_SESSIONS = "user:sessions:{user_id}"


class ValidationLimits:
    """Validation limits and constraints."""
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 100
    MIN_AGE = 0
    MAX_AGE = 150
    MAX_EMAIL_LENGTH = 255
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    
    # Pagination limits
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 1000
    
    # File upload limits
    MAX_FILE_SIZE_MB = 10
    ALLOWED_FILE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf', '.txt']
    
    # Image processing limits
    MAX_IMAGE_SIZE_MB = 5
    MAX_BASE64_SIZE_MB = 7  # Base64 is ~33% larger than binary
    ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png']
    MIN_IMAGE_DIMENSION = 50  # Minimum width/height in pixels
    MAX_IMAGE_DIMENSION = 4096  # Maximum width/height in pixels


class Messages:
    """Application messages and text constants."""
    
    # Success messages
    USER_CREATED = "User created successfully"
    USER_UPDATED = "User updated successfully"
    USER_DELETED = "User deleted successfully"
    USER_ACTIVATED = "User activated successfully"
    USER_DEACTIVATED = "User deactivated successfully"
    
    # Error messages
    INVALID_EMAIL = "Invalid email format"
    EMAIL_ALREADY_EXISTS = "Email already exists"
    USER_NOT_FOUND = "User not found"
    INVALID_AGE = f"Age must be between {ValidationLimits.MIN_AGE} and {ValidationLimits.MAX_AGE}"
    INVALID_NAME_LENGTH = f"Name must be between {ValidationLimits.MIN_NAME_LENGTH} and {ValidationLimits.MAX_NAME_LENGTH} characters"
    CANNOT_DELETE_ACTIVE_USER = "Cannot delete active user"
    
    # Validation messages
    FIELD_REQUIRED = "{field} is required"
    FIELD_TOO_SHORT = "{field} must be at least {min_length} characters"
    FIELD_TOO_LONG = "{field} cannot exceed {max_length} characters"
    
    # Image processing messages
    IMAGE_REQUIRED = "Image data is required"
    INVALID_BASE64 = "Invalid base64 image data"
    IMAGE_TOO_LARGE = f"Image size cannot exceed {ValidationLimits.MAX_IMAGE_SIZE_MB}MB"
    UNSUPPORTED_IMAGE_TYPE = "Unsupported image type. Allowed types: JPEG, PNG"
    LLM_SERVICE_ERROR = "Failed to process image with LLM service"
    LLM_SERVICE_TIMEOUT = "LLM service request timed out"
    TEXT_EXTRACTION_FAILED = "Failed to extract text from image"


class DefaultValues:
    """Default values for various configurations."""
    
    # User defaults
    USER_IS_ACTIVE = True
    USER_DEFAULT_ROLE = "user"
    
    # Pagination defaults
    DEFAULT_SKIP = 0
    DEFAULT_LIMIT = ValidationLimits.DEFAULT_PAGE_SIZE
    
    # Timeout defaults (in seconds)
    DEFAULT_REQUEST_TIMEOUT = 30
    DEFAULT_DATABASE_TIMEOUT = 10
    DEFAULT_CACHE_TTL = 300  # 5 minutes


class RegexPatterns:
    """Regular expression patterns for validation."""
    EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    NAME = r'^[a-zA-Z\s\-\'\.]+$'
    PHONE = r'^\+?1?\d{9,15}$'
    UUID = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'


class AppConfig:
    """Application configuration class."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.environment = Environment(os.getenv('ENVIRONMENT', Environment.DEVELOPMENT.value))
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        self.app_name = os.getenv('APP_NAME', '4IR Backend Project Summit')
        self.app_version = os.getenv('APP_VERSION', '1.0.0')
        
        # Database configuration
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
        self.database_timeout = int(os.getenv('DATABASE_TIMEOUT', str(DefaultValues.DEFAULT_DATABASE_TIMEOUT)))
        
        # Cache configuration
        self.cache_url = os.getenv('CACHE_URL', 'redis://localhost:6379/0')
        self.cache_ttl = int(os.getenv('CACHE_TTL', str(DefaultValues.DEFAULT_CACHE_TTL)))
        
        # Security configuration
        self.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
        self.jwt_expiry_hours = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
        
        # Logging configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'logs/app.log')
        
        # API configuration
        self.api_prefix = os.getenv('API_PREFIX', '/api/v1')
        self.cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
        
        # External services
        self.external_api_key = os.getenv('EXTERNAL_API_KEY')
        self.external_api_url = os.getenv('EXTERNAL_API_URL')
        
        # LLM Service configuration
        self.llm_api_url = os.getenv('LLM_API_URL', 'https://sage.paastry.sysco.net/api/sysco-gen-ai-platform/agents/v1/content/generic/answer')
        self.llm_ai_agent_id = os.getenv('LLM_AI_AGENT_ID', '68d434931b0ad4d414b4978e')
        self.llm_user_agent = os.getenv('LLM_USER_AGENT', 'insomnium/1.3.0')
        self.llm_request_timeout = int(os.getenv('LLM_REQUEST_TIMEOUT', '60'))  # 60 seconds for LLM processing
        self.llm_max_retries = int(os.getenv('LLM_MAX_RETRIES', '3'))
        self.llm_configuration_environment = os.getenv('LLM_CONFIGURATION_ENVIRONMENT', 'DEV')
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == Environment.PRODUCTION
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration dictionary."""
        return {
            'url': self.database_url,
            'timeout': self.database_timeout,
            'pool_size': 20 if self.is_production() else 5,
            'echo': self.debug and not self.is_production()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'environment': self.environment.value,
            'debug': self.debug,
            'app_name': self.app_name,
            'app_version': self.app_version,
            'database_url': '***' if self.is_production() else self.database_url,
            'cache_url': '***' if self.is_production() else self.cache_url,
            'secret_key': '***',
            'log_level': self.log_level,
            'api_prefix': self.api_prefix,
            'llm_api_url': self.llm_api_url,
            'llm_ai_agent_id': self.llm_ai_agent_id,
            'llm_configuration_environment': self.llm_configuration_environment
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM service configuration dictionary."""
        return {
            'api_url': self.llm_api_url,
            'ai_agent_id': self.llm_ai_agent_id,
            'user_agent': self.llm_user_agent,
            'timeout': self.llm_request_timeout,
            'max_retries': self.llm_max_retries,
            'configuration_environment': self.llm_configuration_environment
        }
