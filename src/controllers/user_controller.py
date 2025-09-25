"""
User controller implementation.
"""

from typing import Dict, Any
from src.controllers import BaseController
from src.services.user_service import UserService


class UserController(BaseController):
    """Controller for User endpoints."""
    
    def __init__(self, service: UserService):
        """Initialize user controller."""
        super().__init__(service)
        self._user_service = service  # Type-specific service
    
    def get_routes(self) -> Dict[str, Any]:
        """Get user controller routes configuration."""
        return {
            "GET /users": self.get_all,
            "GET /users/{id}": self.get_by_id,
            "POST /users": self.create,
            "PUT /users/{id}": self.update,
            "DELETE /users/{id}": self.delete,
            "GET /users/email/{email}": self.get_by_email,
            "GET /users/active": self.get_active_users,
            "GET /users/adults": self.get_adults,
            "PUT /users/{id}/activate": self.activate_user,
            "PUT /users/{id}/deactivate": self.deactivate_user,
        }
    
    async def get_by_email(self, email: str) -> Dict[str, Any]:
        """Handle GET request for user by email."""
        try:
            user = await self._user_service.get_by_email(email)
            
            if not user:
                return self._not_found_response(f"User not found with email: {email}")
            
            return self._success_response(self._serialize_entity(user))
            
        except Exception as e:
            return self._error_response(str(e))
    
    async def get_active_users(self) -> Dict[str, Any]:
        """Handle GET request for active users."""
        try:
            users = await self._user_service.get_active_users()
            serialized_users = [self._serialize_entity(user) for user in users]
            
            return self._success_response({
                "items": serialized_users,
                "total": len(serialized_users)
            })
            
        except Exception as e:
            return self._error_response(str(e))
    
    async def get_adults(self) -> Dict[str, Any]:
        """Handle GET request for adult users."""
        try:
            users = await self._user_service.get_adults()
            serialized_users = [self._serialize_entity(user) for user in users]
            
            return self._success_response({
                "items": serialized_users,
                "total": len(serialized_users)
            })
            
        except Exception as e:
            return self._error_response(str(e))
    
    async def activate_user(self, user_id: str) -> Dict[str, Any]:
        """Handle PUT request to activate user."""
        try:
            user = await self._user_service.activate_user(user_id)
            
            if not user:
                return self._not_found_response(f"User not found: {user_id}")
            
            return self._success_response(self._serialize_entity(user))
            
        except Exception as e:
            return self._error_response(str(e))
    
    async def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Handle PUT request to deactivate user."""
        try:
            user = await self._user_service.deactivate_user(user_id)
            
            if not user:
                return self._not_found_response(f"User not found: {user_id}")
            
            return self._success_response(self._serialize_entity(user))
            
        except Exception as e:
            return self._error_response(str(e))
    
    def _serialize_entity(self, entity) -> Dict[str, Any]:
        """Serialize user entity for response."""
        return entity.to_dict()