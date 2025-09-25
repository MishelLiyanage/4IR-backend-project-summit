"""
Base model classes and utilities.
"""

from abc import ABC
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


class BaseModel(ABC):
    """Base model class with common fields and methods."""
    
    def __init__(self, id: Optional[str] = None, created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None):
        """Initialize base model."""
        self.id = id or str(uuid.uuid4())
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    def __eq__(self, other):
        """Check equality based on ID."""
        if not isinstance(other, BaseModel):
            return False
        return self.id == other.id
    
    def __hash__(self):
        """Hash based on ID."""
        return hash(self.id)
    
    def __repr__(self):
        """String representation."""
        return f"{self.__class__.__name__}(id={self.id})"