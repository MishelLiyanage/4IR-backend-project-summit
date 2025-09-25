"""
Base interfaces for the clean architecture pattern.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

# Generic type for model entities
T = TypeVar('T')


class IRepository(Generic[T], ABC):
    """Base repository interface for data access layer."""
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def update(self, entity_id: str, entity: T) -> Optional[T]:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        pass
    
    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        pass


class IService(Generic[T], ABC):
    """Base service interface for business logic layer."""
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID with business logic."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with business logic."""
        pass
    
    @abstractmethod
    async def create(self, entity_data: Dict[str, Any]) -> T:
        """Create entity with business logic and validation."""
        pass
    
    @abstractmethod
    async def update(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[T]:
        """Update entity with business logic and validation."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete entity with business logic."""
        pass


class IController(ABC):
    """Base controller interface for presentation layer."""
    
    @abstractmethod
    def get_routes(self) -> Dict[str, Any]:
        """Get controller routes configuration."""
        pass


class IUnitOfWork(ABC):
    """Unit of Work interface for transaction management."""
    
    @abstractmethod
    async def __aenter__(self):
        """Enter async context manager."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        pass
    
    @abstractmethod
    async def commit(self):
        """Commit the transaction."""
        pass
    
    @abstractmethod
    async def rollback(self):
        """Rollback the transaction."""
        pass