"""
Base repository implementation with common functionality.
"""

from abc import ABC
from typing import Any, Dict, List, Optional, TypeVar, Generic
from src.interfaces import IRepository

T = TypeVar('T')


class BaseRepository(IRepository[T], ABC):
    """Base repository with common CRUD operations."""
    
    def __init__(self):
        """Initialize the repository."""
        self._data: Dict[str, T] = {}  # In-memory storage for demo
    
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        return self._data.get(entity_id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        items = list(self._data.values())
        return items[skip:skip + limit]
    
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        entity_id = self._generate_id(entity)
        self._data[entity_id] = entity
        return entity
    
    async def update(self, entity_id: str, entity: T) -> Optional[T]:
        """Update an existing entity."""
        if entity_id in self._data:
            self._data[entity_id] = entity
            return entity
        return None
    
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        if entity_id in self._data:
            del self._data[entity_id]
            return True
        return False
    
    async def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        return entity_id in self._data
    
    def _generate_id(self, entity: T) -> str:
        """Generate ID for entity. Override in subclasses."""
        return str(len(self._data) + 1)