"""
User model for demonstration purposes.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from src.models import BaseModel


class User(BaseModel):
    """User model with user-specific fields."""
    
    def __init__(
        self, 
        email: str,
        name: str,
        age: Optional[int] = None,
        is_active: bool = True,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """Initialize user model."""
        super().__init__(id, created_at, updated_at)
        self.email = email
        self.name = name
        self.age = age
        self.is_active = is_active
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        data = super().to_dict()
        data.update({
            "email": self.email,
            "name": self.name,
            "age": self.age,
            "is_active": self.is_active
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary."""
        return cls(
            id=data.get('id'),
            email=data['email'],
            name=data['name'],
            age=data.get('age'),
            is_active=data.get('is_active', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
    
    def is_adult(self) -> bool:
        """Check if user is an adult."""
        return self.age is not None and self.age >= 18
    
    def activate(self):
        """Activate the user."""
        self.is_active = True
        self.update_timestamp()
    
    def deactivate(self):
        """Deactivate the user."""
        self.is_active = False
        self.update_timestamp()
    
    def update_profile(self, name: Optional[str] = None, age: Optional[int] = None):
        """Update user profile information."""
        if name is not None:
            self.name = name
        if age is not None:
            self.age = age
        self.update_timestamp()
    
    def __str__(self):
        """String representation of user."""
        status = "Active" if self.is_active else "Inactive"
        return f"User(id={self.id}, email={self.email}, name={self.name}, status={status})"