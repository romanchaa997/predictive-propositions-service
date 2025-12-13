"""User repository for user entity data access."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import User
from .base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""
    
    def __init__(self, db: Session):
        """Initialize with database session and User model."""
        super().__init__(db, User)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User object or None if not found
        """
        try:
            return self.db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            User object or None if not found
        """
        try:
            return self.db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of active User objects
        """
        try:
            return self.db.query(User).filter(
                User.is_active == True
            ).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting active users: {str(e)}")
            return []
    
    def get_inactive_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all inactive users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of inactive User objects
        """
        try:
            return self.db.query(User).filter(
                User.is_active == False
            ).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting inactive users: {str(e)}")
            return []
    
    def count_active_users(self) -> int:
        """Count total number of active users.
        
        Returns:
            Count of active users
        """
        try:
            return self.db.query(User).filter(User.is_active == True).count()
        except Exception as e:
            logger.error(f"Error counting active users: {str(e)}")
            return 0
    
    def deactivate_user(self, user_id) -> bool:
        """Deactivate a user account.
        
        Args:
            user_id: User ID to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.read(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return False
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            self.db.add(user)
            self.db.commit()
            logger.info(f"Deactivated user {user_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deactivating user: {str(e)}")
            raise
    
    def reactivate_user(self, user_id) -> bool:
        """Reactivate a user account.
        
        Args:
            user_id: User ID to reactivate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.read(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return False
            
            user.is_active = True
            user.updated_at = datetime.utcnow()
            self.db.add(user)
            self.db.commit()
            logger.info(f"Reactivated user {user_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reactivating user: {str(e)}")
            raise
    
    def search_users(self, query: str, limit: int = 10) -> List[User]:
        """Search users by username or email.
        
        Args:
            query: Search query string
            limit: Maximum results to return
            
        Returns:
            List of matching User objects
        """
        try:
            search_pattern = f"%{query}%"
            return self.db.query(User).filter(
                (User.username.ilike(search_pattern)) | 
                (User.email.ilike(search_pattern))
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            return []
    
    def get_users_created_after(self, date: datetime) -> List[User]:
        """Get users created after a specific date.
        
        Args:
            date: Cutoff datetime
            
        Returns:
            List of User objects created after the date
        """
        try:
            return self.db.query(User).filter(
                User.created_at >= date
            ).all()
        except Exception as e:
            logger.error(f"Error getting users created after date: {str(e)}")
            return []
