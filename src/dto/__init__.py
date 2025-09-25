"""
Data Transfer Objects (DTOs) for API request/response handling.
"""

from abc import ABC
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass


class BaseDTO(ABC):
    """Base DTO class with common serialization methods."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        if hasattr(self, '__dataclass_fields__'):
            return {
                field.name: getattr(self, field.name) 
                for field in self.__dataclass_fields__.values()
                if getattr(self, field.name, None) is not None
            }
        return self.__dict__.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create DTO from dictionary. Should be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement from_dict method")


@dataclass
class UserCreateDTO(BaseDTO):
    """DTO for creating a new user."""
    email: str
    name: str
    age: Optional[int] = None
    is_active: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserCreateDTO':
        """Create UserCreateDTO from dictionary."""
        return cls(
            email=data['email'],
            name=data['name'],
            age=data.get('age'),
            is_active=data.get('is_active', True)
        )


@dataclass
class UserUpdateDTO(BaseDTO):
    """DTO for updating an existing user."""
    email: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    is_active: Optional[bool] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserUpdateDTO':
        """Create UserUpdateDTO from dictionary."""
        return cls(
            email=data.get('email'),
            name=data.get('name'),
            age=data.get('age'),
            is_active=data.get('is_active')
        )


@dataclass
class UserResponseDTO(BaseDTO):
    """DTO for user response data."""
    id: str
    email: str
    name: str
    age: Optional[int]
    is_active: bool
    created_at: str
    updated_at: str
    
    @classmethod
    def from_user(cls, user) -> 'UserResponseDTO':
        """Create UserResponseDTO from User model."""
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            age=user.age,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else "",
            updated_at=user.updated_at.isoformat() if user.updated_at else ""
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserResponseDTO':
        """Create UserResponseDTO from dictionary."""
        return cls(
            id=data['id'],
            email=data['email'],
            name=data['name'],
            age=data.get('age'),
            is_active=data['is_active'],
            created_at=data['created_at'],
            updated_at=data['updated_at']
        )


@dataclass
class PaginationDTO(BaseDTO):
    """DTO for pagination parameters."""
    skip: int = 0
    limit: int = 20
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaginationDTO':
        """Create PaginationDTO from dictionary."""
        return cls(
            skip=max(0, data.get('skip', 0)),
            limit=min(1000, max(1, data.get('limit', 20)))
        )


@dataclass
class PaginatedResponseDTO(BaseDTO):
    """DTO for paginated response data."""
    items: list
    total: int
    skip: int
    limit: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(cls, items: list, total: int, skip: int, limit: int) -> 'PaginatedResponseDTO':
        """Create paginated response DTO."""
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_next=skip + limit < total,
            has_previous=skip > 0
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaginatedResponseDTO':
        """Create PaginatedResponseDTO from dictionary."""
        return cls(
            items=data['items'],
            total=data['total'],
            skip=data['skip'],
            limit=data['limit'],
            has_next=data['has_next'],
            has_previous=data['has_previous']
        )


@dataclass
class ErrorResponseDTO(BaseDTO):
    """DTO for error response data."""
    message: str
    code: str
    type: str
    details: Dict[str, Any]
    timestamp: str
    
    @classmethod
    def from_exception(cls, exception) -> 'ErrorResponseDTO':
        """Create ErrorResponseDTO from exception."""
        if hasattr(exception, 'to_dict'):
            error_data = exception.to_dict()
            return cls(
                message=error_data.get('message', str(exception)),
                code=error_data.get('code', 'UNKNOWN_ERROR'),
                type=error_data.get('type', type(exception).__name__),
                details=error_data.get('details', {}),
                timestamp=datetime.utcnow().isoformat()
            )
        
        return cls(
            message=str(exception),
            code='UNKNOWN_ERROR',
            type=type(exception).__name__,
            details={},
            timestamp=datetime.utcnow().isoformat()
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorResponseDTO':
        """Create ErrorResponseDTO from dictionary."""
        return cls(
            message=data['message'],
            code=data['code'],
            type=data['type'],
            details=data.get('details', {}),
            timestamp=data.get('timestamp', datetime.utcnow().isoformat())
        )
