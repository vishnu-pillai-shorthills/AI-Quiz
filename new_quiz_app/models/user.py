"""
User model representing authenticated users
"""
from datetime import datetime
from typing import Dict, Optional
from bson import ObjectId

class User:
    """Model representing an authenticated user"""
    
    def __init__(self, user_id: str, email: str, name: str = None, given_name: str = None, family_name: str = None):
        self.user_id = user_id
        self.email = email
        self.name = name or "Unknown User"
        self.given_name = given_name or ""
        self.family_name = family_name or ""
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
        self.is_active = True
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary for database storage"""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'name': self.name,
            'given_name': self.given_name,
            'family_name': self.family_name,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create user instance from dictionary"""
        user = cls(
            user_id=data['user_id'],
            email=data['email'],
            name=data.get('name'),
            given_name=data.get('given_name'),
            family_name=data.get('family_name')
        )
        
        if '_id' in data:
            user.id = str(data['_id'])
        
        if 'created_at' in data:
            user.created_at = data['created_at']
        
        if 'last_active' in data:
            user.last_active = data['last_active']
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        return user
    
    def update_last_active(self):
        """Update last active timestamp"""
        self.last_active = datetime.utcnow()
    
    def get_full_name(self) -> str:
        """Get user's full name"""
        if self.given_name and self.family_name:
            return f"{self.given_name} {self.family_name}"
        elif self.given_name:
            return self.given_name
        elif self.family_name:
            return self.family_name
        else:
            return self.name
    
    def get_display_name(self) -> str:
        """Get display name (full name or email if no name)"""
        full_name = self.get_full_name()
        if full_name and full_name != "Unknown User":
            return full_name
        return self.email
    
    def validate(self) -> list:
        """Validate user data and return list of errors"""
        errors = []
        
        if not self.user_id:
            errors.append("User ID is required")
        
        if not self.email:
            errors.append("Email is required")
        elif '@' not in self.email:
            errors.append("Invalid email format")
        
        if not self.name:
            errors.append("Name is required")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if user is valid"""
        return len(self.validate()) == 0
    
    def __repr__(self):
        return f"<User {self.email} ({self.user_id})>" 