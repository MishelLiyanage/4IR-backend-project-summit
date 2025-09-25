"""
User repository implementation.
"""

from typing import List, Optional
from src.repositories import BaseRepository
from src.models.user import User


class UserRepository(BaseRepository[User]):
    """Repository for User entities."""
    
    def __init__(self):
        """Initialize user repository."""
        super().__init__()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        for user in self._data.values():
            if user.email == email:
                return user
        return None
    
    async def get_active_users(self) -> List[User]:
        """Get all active users."""
        return [user for user in self._data.values() if user.is_active]
    
    async def get_users_by_age_range(self, min_age: int, max_age: int) -> List[User]:
        """Get users within age range."""
        return [
            user for user in self._data.values() 
            if user.age is not None and min_age <= user.age <= max_age
        ]
    
    def _generate_id(self, entity: User) -> str:
        """Generate ID for user entity."""
        return entity.id  # Users already have UUID from BaseModel