"""
Base controller implementation with common HTTP handling.
"""

from abc import ABC
from typing import Any, Dict, Optional
import logging
from src.interfaces import IController, IService

logger = logging.getLogger(__name__)


class BaseController(IController, ABC):
    """Base controller with common HTTP request handling."""
    
    def __init__(self, service: IService):
        """Initialize controller with service dependency."""
        self._service = service
    
    def get_routes(self) -> Dict[str, Any]:
        """Get controller routes configuration. Override in subclasses."""
        return {}
    
    async def get_by_id(self, entity_id: str) -> Dict[str, Any]:
        """Handle GET request for single entity."""
        try:
            logger.info(f"Controller: Getting entity by ID: {entity_id}")
            
            entity = await self._service.get_by_id(entity_id)
            
            if not entity:
                return self._not_found_response(f"Entity not found: {entity_id}")
            
            return self._success_response(self._serialize_entity(entity))
            
        except Exception as e:
            logger.error(f"Error getting entity by ID: {e}")
            return self._error_response(str(e))
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Handle GET request for all entities."""
        try:
            logger.info(f"Controller: Getting all entities - skip: {skip}, limit: {limit}")
            
            entities = await self._service.get_all(skip, limit)
            
            serialized_entities = [self._serialize_entity(entity) for entity in entities]
            
            return self._success_response({
                "items": serialized_entities,
                "skip": skip,
                "limit": limit,
                "total": len(serialized_entities)
            })
            
        except Exception as e:
            logger.error(f"Error getting all entities: {e}")
            return self._error_response(str(e))
    
    async def create(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle POST request to create entity."""
        try:
            logger.info("Controller: Creating new entity")
            
            entity = await self._service.create(entity_data)
            
            return self._created_response(self._serialize_entity(entity))
            
        except ValueError as e:
            logger.warning(f"Validation error creating entity: {e}")
            return self._bad_request_response(str(e))
        except Exception as e:
            logger.error(f"Error creating entity: {e}")
            return self._error_response(str(e))
    
    async def update(self, entity_id: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PUT request to update entity."""
        try:
            logger.info(f"Controller: Updating entity with ID: {entity_id}")
            
            entity = await self._service.update(entity_id, entity_data)
            
            if not entity:
                return self._not_found_response(f"Entity not found: {entity_id}")
            
            return self._success_response(self._serialize_entity(entity))
            
        except ValueError as e:
            logger.warning(f"Validation error updating entity: {e}")
            return self._bad_request_response(str(e))
        except Exception as e:
            logger.error(f"Error updating entity: {e}")
            return self._error_response(str(e))
    
    async def delete(self, entity_id: str) -> Dict[str, Any]:
        """Handle DELETE request for entity."""
        try:
            logger.info(f"Controller: Deleting entity with ID: {entity_id}")
            
            success = await self._service.delete(entity_id)
            
            if not success:
                return self._not_found_response(f"Entity not found: {entity_id}")
            
            return self._no_content_response()
            
        except Exception as e:
            logger.error(f"Error deleting entity: {e}")
            return self._error_response(str(e))
    
    def _serialize_entity(self, entity) -> Dict[str, Any]:
        """Serialize entity for response. Override in subclasses."""
        if hasattr(entity, '__dict__'):
            return entity.__dict__
        return {"data": str(entity)}
    
    def _success_response(self, data: Any) -> Dict[str, Any]:
        """Create success response."""
        return {
            "status": "success",
            "status_code": 200,
            "data": data
        }
    
    def _created_response(self, data: Any) -> Dict[str, Any]:
        """Create created response."""
        return {
            "status": "success",
            "status_code": 201,
            "data": data
        }
    
    def _no_content_response(self) -> Dict[str, Any]:
        """Create no content response."""
        return {
            "status": "success",
            "status_code": 204,
            "data": None
        }
    
    def _not_found_response(self, message: str) -> Dict[str, Any]:
        """Create not found response."""
        return {
            "status": "error",
            "status_code": 404,
            "error": {
                "message": message,
                "type": "NotFound"
            }
        }
    
    def _bad_request_response(self, message: str) -> Dict[str, Any]:
        """Create bad request response."""
        return {
            "status": "error",
            "status_code": 400,
            "error": {
                "message": message,
                "type": "BadRequest"
            }
        }
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create internal server error response."""
        return {
            "status": "error",
            "status_code": 500,
            "error": {
                "message": message,
                "type": "InternalServerError"
            }
        }