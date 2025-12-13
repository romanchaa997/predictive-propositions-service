feature_engineering.py"""Feature engineering pipeline for ML model training."""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from uuid import UUID

from storage.repositories import (
    UserRepository,
    UserFeatureRepository,
    InteractionRepository,
    PropositionRepository,
    FeatureRepository
)
from storage.models import UserFeature, Feature

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Handles feature engineering for ML model training."""
    
    def __init__(self, db: Session, lookback_days: int = 30):
        """Initialize feature engineer.
        
        Args:
            db: SQLAlchemy session
            lookback_days: Days of history to use for feature engineering
        """
        self.db = db
        self.lookback_days = lookback_days
        self.user_repo = UserRepository(db)
        self.interaction_repo = InteractionRepository(db)
        self.proposition_repo = PropositionRepository(db)
        self.feature_repo = FeatureRepository(db)
        self.user_feature_repo = UserFeatureRepository(db)
    
    def engineer_all_features(self, user_id: UUID) -> Dict[str, float]:
        """Engineer all features for a user.
        
        Args:
            user_id: User ID to engineer features for
            
        Returns:
            Dictionary of feature_name: feature_value
        """
        logger.info(f"Engineering features for user {user_id}")
        
        features = {}
        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)
        
        # User engagement features
        features.update(self._engineer_engagement_features(user_id, cutoff_date))
        
        # Interaction pattern features
        features.update(self._engineer_interaction_features(user_id, cutoff_date))
        
        # Proposition response features
        features.update(self._engineer_proposition_features(user_id, cutoff_date))
        
        # Temporal features
        features.update(self._engineer_temporal_features(user_id))
        
        logger.info(f"Engineered {len(features)} features for user {user_id}")
        return features
    
    def _engineer_engagement_features(self, user_id: UUID, cutoff_date: datetime) -> Dict[str, float]:
        """Engineer user engagement features."""
        interactions = self.interaction_repo.get_interactions_by_user(
            user_id, after_date=cutoff_date
        )
        
        total_interactions = len(interactions)
        click_count = sum(1 for i in interactions if i.interaction_type == 'click')
        hover_count = sum(1 for i in interactions if i.interaction_type == 'hover')
        accept_count = sum(1 for i in interactions if i.interaction_type == 'accept')
        reject_count = sum(1 for i in interactions if i.interaction_type == 'reject')
        
        # Calculate engagement rates
        engagement_rate = click_count / total_interactions if total_interactions > 0 else 0
        acceptance_rate = accept_count / total_interactions if total_interactions > 0 else 0
        rejection_rate = reject_count / total_interactions if total_interactions > 0 else 0
        
        # Calculate average interaction duration
        durations = [i.duration_seconds for i in interactions if i.duration_seconds]
        avg_duration = np.mean(durations) if durations else 0
        
        return {
            "total_interactions": float(total_interactions),
            "click_count": float(click_count),
            "hover_count": float(hover_count),
            "accept_count": float(accept_count),
            "reject_count": float(reject_count),
            "engagement_rate": float(engagement_rate),
            "acceptance_rate": float(acceptance_rate),
            "rejection_rate": float(rejection_rate),
            "avg_interaction_duration": float(avg_duration)
        }
    
    def _engineer_interaction_features(self, user_id: UUID, cutoff_date: datetime) -> Dict[str, float]:
        """Engineer interaction pattern features."""
        interactions = self.interaction_repo.get_interactions_by_user(
            user_id, after_date=cutoff_date
        )
        
        # Calculate interaction frequency
        if interactions:
            date_range = (interactions[-1].created_at - interactions[0].created_at).days + 1
            interaction_frequency = len(interactions) / max(date_range, 1)
        else:
            interaction_frequency = 0
        
        # Calculate interaction diversity
        interaction_types = set(i.interaction_type for i in interactions)
        interaction_diversity = len(interaction_types) / 5  # Normalize by max types
        
        return {
            "interaction_frequency": float(interaction_frequency),
            "interaction_diversity": float(interaction_diversity),
            "unique_interaction_types": float(len(interaction_types))
        }
    
    def _engineer_proposition_features(self, user_id: UUID, cutoff_date: datetime) -> Dict[str, float]:
        """Engineer proposition response features."""
        propositions = self.proposition_repo.get_propositions_by_user(user_id)
        recent_props = [p for p in propositions if p.created_at >= cutoff_date]
        
        # Calculate proposition response statistics
        avg_confidence = np.mean([p.confidence_score for p in recent_props]) if recent_props else 0
        max_confidence = max([p.confidence_score for p in recent_props]) if recent_props else 0
        
        # Proposition status distribution
        pending = sum(1 for p in recent_props if p.status == 'pending')
        accepted = sum(1 for p in recent_props if p.status == 'accepted')
        rejected = sum(1 for p in recent_props if p.status == 'rejected')
        
        # Proposition type distribution
        prop_types = {}
        for p in recent_props:
            prop_type = p.proposition_type
            prop_types[f"type_{prop_type}"] = prop_types.get(f"type_{prop_type}", 0) + 1
        
        return {
            "avg_proposition_confidence": float(avg_confidence),
            "max_proposition_confidence": float(max_confidence),
            "pending_propositions": float(pending),
            "accepted_propositions": float(accepted),
            "rejected_propositions": float(rejected),
            "total_propositions": float(len(recent_props)),
            **{k: float(v) for k, v in prop_types.items()}
        }
    
    def _engineer_temporal_features(self, user_id: UUID) -> Dict[str, float]:
        """Engineer temporal features."""
        user = self.user_repo.read(user_id)
        if not user:
            return {}
        
        now = datetime.utcnow()
        account_age_days = (now - user.created_at).days
        
        return {
            "account_age_days": float(account_age_days),
            "is_active": float(user.is_active),
            "days_since_last_update": float((now - user.updated_at).days)
        }
    
    def store_features(self, user_id: UUID, features: Dict[str, float]) -> None:
        """Store engineered features in database.
        
        Args:
            user_id: User ID
            features: Dictionary of feature_name: feature_value
        """
        logger.info(f"Storing {len(features)} features for user {user_id}")
        
        for feature_name, feature_value in features.items():
            # Get or create feature definition
            feature = self.feature_repo.get_by_name(feature_name)
            if not feature:
                feature = self.feature_repo.create({
                    "name": feature_name,
                    "feature_type": "numeric",
                    "description": f"Feature: {feature_name}",
                    "is_active": True
                })
            
            # Store user feature value
            self.user_feature_repo.create({
                "user_id": user_id,
                "feature_id": feature.id,
                "value": str(feature_value),
                "timestamp": datetime.utcnow()
            })
    
    def get_training_data(self, limit: int = 1000) -> Tuple[List[Dict], List[float]]:
        """Get feature vectors and labels for model training.
        
        Args:
            limit: Maximum number of samples
            
        Returns:
            Tuple of (feature_vectors, labels)
        """
        logger.info(f"Preparing training data for {limit} users")
        
        users = self.user_repo.read_all(limit=limit)
        X = []  # Feature vectors
        y = []  # Labels (acceptance rate)
        
        for user in users:
            features = self.engineer_all_features(user.id)
            interactions = self.interaction_repo.get_interactions_by_user(user.id)
            
            if interactions:
                accept_count = sum(1 for i in interactions if i.interaction_type == 'accept')
                label = accept_count / len(interactions)  # Acceptance rate
            else:
                label = 0.5  # Default label
            
            X.append(features)
            y.append(label)
        
        logger.info(f"Prepared training data: {len(X)} samples")
        return X, y
    
    def normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Normalize features to 0-1 range.
        
        Args:
            features: Dictionary of feature_name: feature_value
            
        Returns:
            Dictionary of normalized features
        """
        normalized = {}
        
        for name, value in features.items():
            if "rate" in name.lower():
                # Already normalized (0-1)
                normalized[name] = value
            elif "days" in name.lower():
                # Normalize days (0-365)
                normalized[name] = min(value / 365, 1.0)
            elif "count" in name.lower():
                # Normalize counts (0-100)
                normalized[name] = min(value / 100, 1.0)
            elif "confidence" in name.lower():
                # Already normalized (0-1)
                normalized[name] = value
            else:
                # Default: min-max normalization
                normalized[name] = min(value / max(value, 1), 1.0)
        
        return normalized


class FeatureStore:
    """Manages feature storage and retrieval."""
    
    def __init__(self, db: Session):
        """Initialize feature store.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
        self.user_feature_repo = UserFeatureRepository(db)
        self.feature_repo = FeatureRepository(db)
    
    def get_user_features(self, user_id: UUID) -> Dict[str, float]:
        """Get latest features for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of feature_name: feature_value
        """
        user_features = self.user_feature_repo.get_user_features(user_id)
        
        features = {}
        for uf in user_features:
            try:
                features[uf.feature.name] = float(uf.value)
            except (ValueError, AttributeError) as e:
                logger.error(f"Error parsing feature {uf.feature.name}: {str(e)}")
        
        return features
    
    def get_feature_vector(self, user_id: UUID) -> List[float]:
        """Get feature vector for a user (for model inference).
        
        Args:
            user_id: User ID
            
        Returns:
            List of feature values
        """
        features = self.get_user_features(user_id)
        all_features = self.feature_repo.read_all()
        
        # Create vector in consistent order
        vector = [features.get(f.name, 0.0) for f in all_features]
        return vector
