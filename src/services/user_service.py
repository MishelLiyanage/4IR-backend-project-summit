"""
User service implementation with business logic.
"""

from typing import Dict, Any, List, Optional
import re
from src.services import BaseService
from src.models.user import User
from src.repositories.user_repository import UserRepository


class UserService(BaseService[User]):
    """Service for User entities with business logic."""
    
    def __init__(self, repository: UserRepository):
        """Initialize user service."""
        super().__init__(repository)
        self._user_repository = repository  # Type-specific repository
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email with business validation."""
        if not self._is_valid_email(email):
            return None
        
        return await self._user_repository.get_by_email(email)
    
    async def get_active_users(self) -> List[User]:
        """Get all active users."""
        return await self._user_repository.get_active_users()
    
    async def get_adults(self) -> List[User]:
        """Get all adult users (18+)."""
        users = await self._user_repository.get_users_by_age_range(18, 150)
        return users
    
    async def activate_user(self, user_id: str) -> Optional[User]:
        """Activate a user account."""
        user = await self._repository.get_by_id(user_id)
        if not user:
            return None
        
        user.activate()
        return await self._repository.update(user_id, user)
    
    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """Deactivate a user account."""
        user = await self._repository.get_by_id(user_id)
        if not user:
            return None
        
        user.deactivate()
        return await self._repository.update(user_id, user)
    
    async def _validate_entity_data(self, entity_data: Dict[str, Any], is_update: bool = False) -> None:
        """Validate user data."""
        await super()._validate_entity_data(entity_data, is_update)
        
        # Required fields for creation
        if not is_update:
            if 'email' not in entity_data:
                raise ValueError("Email is required")
            if 'name' not in entity_data:
                raise ValueError("Name is required")
        
        # Validate email format
        if 'email' in entity_data and not self._is_valid_email(entity_data['email']):
            raise ValueError("Invalid email format")
        
        # Validate age
        if 'age' in entity_data:
            age = entity_data['age']
            if age is not None and (not isinstance(age, int) or age < 0 or age > 150):
                raise ValueError("Age must be between 0 and 150")
        
        # Validate name
        if 'name' in entity_data:
            name = entity_data['name']
            if not isinstance(name, str) or len(name.strip()) < 2:
                raise ValueError("Name must be at least 2 characters long")
        
        # Check for duplicate email (only for creation or email change)
        if 'email' in entity_data:
            existing_user = await self._user_repository.get_by_email(entity_data['email'])
            if existing_user and (not is_update or existing_user.id != entity_data.get('id')):
                raise ValueError("Email already exists")
    
    async def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> User:
        """Create user from data."""
        return User(
            email=entity_data['email'],
            name=entity_data['name'],
            age=entity_data.get('age'),
            is_active=entity_data.get('is_active', True)
        )
    
    async def _update_entity_from_data(self, existing_entity: User, entity_data: Dict[str, Any]) -> User:
        """Update user from data."""
        if 'email' in entity_data:
            existing_entity.email = entity_data['email']
        if 'name' in entity_data:
            existing_entity.name = entity_data['name']
        if 'age' in entity_data:
            existing_entity.age = entity_data['age']
        if 'is_active' in entity_data:
            existing_entity.is_active = entity_data['is_active']
        
        existing_entity.update_timestamp()
        return existing_entity
    
    async def _can_delete_entity(self, entity_id: str) -> bool:
        """Check if user can be deleted."""
        user = await self._repository.get_by_id(entity_id)
        if not user:
            return False
        
        # Business rule: Can only delete inactive users
        return not user.is_active
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        if not email or not isinstance(email, str):
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None