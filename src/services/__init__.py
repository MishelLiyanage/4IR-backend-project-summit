"""
Base service implementation with common business logic.
"""

from abc import ABC
from typing import Any, Dict, List, Optional, TypeVar, Generic
import logging
from src.interfaces import IService, IRepository

T = TypeVar('T')
logger = logging.getLogger(__name__)


class BaseService(IService[T], ABC):
    """Base service with common business logic operations."""
    
    def __init__(self, repository: IRepository[T]):
        """Initialize service with repository dependency."""
        self._repository = repository
    
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID with business logic."""
        logger.info(f"Getting entity by ID: {entity_id}")
        
        if not entity_id:
            logger.warning("Entity ID cannot be empty")
            return None
        
        entity = await self._repository.get_by_id(entity_id)
        if not entity:
            logger.warning(f"Entity not found with ID: {entity_id}")
        
        return entity
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with business logic."""
        logger.info(f"Getting all entities - skip: {skip}, limit: {limit}")
        
        # Validate pagination parameters
        if skip < 0:
            skip = 0
        if limit <= 0 or limit > 1000:
            limit = 100
        
        return await self._repository.get_all(skip, limit)
    
    async def create(self, entity_data: Dict[str, Any]) -> T:
        """Create entity with business logic and validation."""
        logger.info("Creating new entity")
        
        # Validate entity data
        await self._validate_entity_data(entity_data)
        
        # Create entity from data
        entity = await self._create_entity_from_data(entity_data)
        
        # Save entity
        created_entity = await self._repository.create(entity)
        
        logger.info("Entity created successfully")
        return created_entity
    
    async def update(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[T]:
        """Update entity with business logic and validation."""
        logger.info(f"Updating entity with ID: {entity_id}")
        
        # Check if entity exists
        existing_entity = await self._repository.get_by_id(entity_id)
        if not existing_entity:
            logger.warning(f"Entity not found for update: {entity_id}")
            return None
        
        # Validate entity data
        await self._validate_entity_data(entity_data, is_update=True)
        
        # Update entity from data
        updated_entity = await self._update_entity_from_data(existing_entity, entity_data)
        
        # Save updated entity
        result = await self._repository.update(entity_id, updated_entity)
        
        logger.info("Entity updated successfully")
        return result
    
    async def delete(self, entity_id: str) -> bool:
        """Delete entity with business logic."""
        logger.info(f"Deleting entity with ID: {entity_id}")
        
        # Check if entity exists
        if not await self._repository.exists(entity_id):
            logger.warning(f"Entity not found for deletion: {entity_id}")
            return False
        
        # Perform business logic checks before deletion
        if not await self._can_delete_entity(entity_id):
            logger.warning(f"Entity cannot be deleted: {entity_id}")
            return False
        
        result = await self._repository.delete(entity_id)
        
        if result:
            logger.info("Entity deleted successfully")
        
        return result
    
    async def _validate_entity_data(self, entity_data: Dict[str, Any], is_update: bool = False) -> None:
        """Validate entity data. Override in subclasses."""
        if not entity_data:
            raise ValueError("Entity data cannot be empty")
    
    async def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> T:
        """Create entity from data. Must be implemented in subclasses."""
        raise NotImplementedError("Subclasses must implement _create_entity_from_data")
    
    async def _update_entity_from_data(self, existing_entity: T, entity_data: Dict[str, Any]) -> T:
        """Update entity from data. Must be implemented in subclasses."""
        raise NotImplementedError("Subclasses must implement _update_entity_from_data")
    
    async def _can_delete_entity(self, entity_id: str) -> bool:
        """Check if entity can be deleted. Override in subclasses."""
        return True