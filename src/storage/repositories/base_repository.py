"""Base repository class providing common CRUD operations."""
from typing import TypeVar, Generic, List, Optional, Type, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_
import uuid
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Generic base repository class for common database operations."""
    
    def __init__(self, db: Session, model: Type[T]):
        """Initialize repository with database session and model.
        
        Args:
            db: SQLAlchemy session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
    
    def create(self, obj_in: Dict[str, Any]) -> T:
        """Create a new record.
        
        Args:
            obj_in: Dictionary containing object data
            
        Returns:
            Created model instance
        """
        try:
            db_obj = self.model(**obj_in)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info(f"Created {self.model.__name__} with id {getattr(db_obj, 'id', None)}")
            return db_obj
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise
    
    def read(self, id: Any) -> Optional[T]:
        """Read a record by ID.
        
        Args:
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except Exception as e:
            logger.error(f"Error reading {self.model.__name__}: {str(e)}")
            return None
    
    def read_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Read all records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of model instances
        """
        try:
            return self.db.query(self.model).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error reading all {self.model.__name__}: {str(e)}")
            return []
    
    def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[T]:
        """Update a record.
        
        Args:
            id: Primary key value
            obj_in: Dictionary with update data
            
        Returns:
            Updated model instance or None if not found
        """
        try:
            db_obj = self.db.query(self.model).filter(self.model.id == id).first()
            if not db_obj:
                logger.warning(f"{self.model.__name__} with id {id} not found")
                return None
            
            for key, value in obj_in.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info(f"Updated {self.model.__name__} with id {id}")
            return db_obj
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {str(e)}")
            raise
    
    def delete(self, id: Any) -> bool:
        """Delete a record.
        
        Args:
            id: Primary key value
            
        Returns:
            True if deleted, False if not found
        """
        try:
            db_obj = self.db.query(self.model).filter(self.model.id == id).first()
            if not db_obj:
                logger.warning(f"{self.model.__name__} with id {id} not found")
                return False
            
            self.db.delete(db_obj)
            self.db.commit()
            logger.info(f"Deleted {self.model.__name__} with id {id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model.__name__}: {str(e)}")
            raise
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records matching optional filters.
        
        Args:
            filters: Optional dictionary of field-value pairs for filtering
            
        Returns:
            Count of matching records
        """
        try:
            query = self.db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)
            
            return query.count()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {str(e)}")
            return 0
    
    def exists(self, id: Any) -> bool:
        """Check if a record exists.
        
        Args:
            id: Primary key value
            
        Returns:
            True if exists, False otherwise
        """
        try:
            return self.db.query(self.model).filter(self.model.id == id).first() is not None
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__}: {str(e)}")
            return False
    
    def filter_by(self, **kwargs) -> List[T]:
        """Filter records by field values.
        
        Args:
            **kwargs: Field-value pairs to filter by
            
        Returns:
            List of matching model instances
        """
        try:
            return self.db.query(self.model).filter_by(**kwargs).all()
        except Exception as e:
            logger.error(f"Error filtering {self.model.__name__}: {str(e)}")
            return []
    
    def order_by(self, field: str, descending: bool = False, **filters) -> List[T]:
        """Get records ordered by field with optional filters.
        
        Args:
            field: Field name to order by
            descending: Sort in descending order if True
            **filters: Optional field-value pairs for filtering
            
        Returns:
            List of ordered model instances
        """
        try:
            query = self.db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)
            
            if hasattr(self.model, field):
                order_col = getattr(self.model, field)
                if descending:
                    query = query.order_by(desc(order_col))
                else:
                    query = query.order_by(asc(order_col))
            
            return query.all()
        except Exception as e:
            logger.error(f"Error ordering {self.model.__name__}: {str(e)}")
            return []
