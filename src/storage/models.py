"""Database models for Predictive Propositions Service."""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Table, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

Base = declarative_base()


class PropositionType(str, Enum):
    """Types of propositions the system can generate."""
    FEATURE_REQUEST = "feature_request"
    OPTIMIZATION = "optimization"
    RISK_ALERT = "risk_alert"
    USER_ENGAGEMENT = "user_engagement"
    CONTENT_RECOMMENDATION = "content_recommendation"


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSONB, nullable=True)
    
    # Relationships
    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")
    features = relationship("UserFeature", back_populates="user", cascade="all, delete-orphan")
    propositions = relationship("Proposition", back_populates="user", cascade="all, delete-orphan")


class Proposition(Base):
    """Proposition model - represents ML-generated suggestions."""
    __tablename__ = "propositions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    proposition_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0.0-1.0
    predicted_engagement = Column(Float, nullable=True)  # Expected engagement probability
    feature_importance = Column(JSONB, nullable=True)  # {"feature_name": importance_score}
    status = Column(String(50), default="pending", index=True)  # pending, accepted, rejected, expired
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="propositions")
    interactions = relationship("Interaction", back_populates="proposition", cascade="all, delete-orphan")
    __table_args__ = (Index("idx_user_type_status", "user_id", "proposition_type", "status"),)


class Interaction(Base):
    """User interaction with propositions (click, hover, accept, reject, etc)."""
    __tablename__ = "interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    proposition_id = Column(UUID(as_uuid=True), ForeignKey("propositions.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False, index=True)  # click, hover, accept, reject, ignore
    duration_seconds = Column(Integer, nullable=True)  # For hover/view interactions
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    metadata_json = Column(JSONB, nullable=True)  # Device info, location, etc
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    proposition = relationship("Proposition", back_populates="interactions")
    __table_args__ = (Index("idx_user_timestamp", "user_id", "created_at"),)


class Feature(Base):
    """Feature definitions for ML model."""
    __tablename__ = "features"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    feature_type = Column(String(50), nullable=False)  # numeric, categorical, text, temporal
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_features = relationship("UserFeature", back_populates="feature", cascade="all, delete-orphan")


class UserFeature(Base):
    """User feature values - time-series data for ML model."""
    __tablename__ = "user_features"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(String(1000), nullable=False)  # Stored as string for flexibility
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="features")
    feature = relationship("Feature", back_populates="user_features")
    __table_args__ = (Index("idx_user_feature_time", "user_id", "feature_id", "timestamp"),)


class ModelPerformance(Base):
    """Track ML model performance metrics over time."""
    __tablename__ = "model_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version = Column(String(50), nullable=False, index=True)
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    auc_roc = Column(Float, nullable=True)
    total_predictions = Column(Integer, default=0)
    true_positives = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    metadata_json = Column(JSONB, nullable=True)
    
    __table_args__ = (Index("idx_model_version_date", "model_version", "created_at"),)
