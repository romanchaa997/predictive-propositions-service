ml_training.py"""ML model training and ranking engine for Predictive Propositions Service."""
import logging
import joblib
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from uuid import UUID
import json

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb

from sqlalchemy.orm import Session
from storage.repositories import (
    FeatureRepository,
    UserFeatureRepository,
    PropositionRepository
)
from storage.models import ModelPerformance
from feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class MLModelTrainer:
    """Handles ML model training and evaluation."""
    
    def __init__(self, db: Session, model_type: str = "xgboost"):
        """Initialize ML trainer.
        
        Args:
            db: SQLAlchemy session
            model_type: Type of model - 'xgboost', 'random_forest', 'gradient_boosting'
        """
        self.db = db
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_version = None
        self.feature_engineer = FeatureEngineer(db)
        self.feature_repo = FeatureRepository(db)
    
    def prepare_training_data(self, limit: int = 1000) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare training data from feature store.
        
        Args:
            limit: Maximum number of samples
            
        Returns:
            Tuple of (X, y, feature_names)
        """
        logger.info(f"Preparing training data for {limit} samples")
        
        X, y = self.feature_engineer.get_training_data(limit=limit)
        
        # Extract feature names from first sample
        if X:
            feature_names = list(X[0].keys())
            self.feature_names = feature_names
            
            # Convert to numpy array
            X_array = np.array([list(sample.values()) for sample in X])
            y_array = np.array(y)
            
            logger.info(f"Prepared {len(X_array)} samples with {len(feature_names)} features")
            return X_array, y_array, feature_names
        
        raise ValueError("No training data available")
    
    def train(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> Dict[str, float]:
        """Train ML model.
        
        Args:
            X: Feature matrix
            y: Target labels
            test_size: Test set proportion
            
        Returns:
            Dictionary of performance metrics
        """
        logger.info(f"Training {self.model_type} model")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Select and train model
        if self.model_type == "xgboost":
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                verbosity=0
            )
        elif self.model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Train on scaled data
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        
        metrics = {
            "mse": float(mean_squared_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "r2": float(r2_score(y_test, y_pred)),
            "train_size": len(X_train),
            "test_size": len(X_test)
        }
        
        logger.info(f"Model trained with R²={metrics['r2']:.4f}")
        return metrics
    
    def save_model(self, model_path: str) -> str:
        """Save trained model and scaler.
        
        Args:
            model_path: Path to save model
            
        Returns:
            Model version string
        """
        if not self.model:
            raise ValueError("No trained model to save")
        
        self.model_version = datetime.utcnow().isoformat()
        
        # Save model and scaler
        joblib.dump(self.model, f"{model_path}_model.pkl")
        joblib.dump(self.scaler, f"{model_path}_scaler.pkl")
        joblib.dump(self.feature_names, f"{model_path}_features.pkl")
        
        logger.info(f"Model saved to {model_path}")
        return self.model_version
    
    def load_model(self, model_path: str) -> None:
        """Load saved model and scaler.
        
        Args:
            model_path: Path to load model from
        """
        self.model = joblib.load(f"{model_path}_model.pkl")
        self.scaler = joblib.load(f"{model_path}_scaler.pkl")
        self.feature_names = joblib.load(f"{model_path}_features.pkl")
        
        logger.info(f"Model loaded from {model_path}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions.
        
        Args:
            X: Feature matrix
            
        Returns:
            Predicted probabilities
        """
        if not self.model:
            raise ValueError("No trained model")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores.
        
        Returns:
            Dictionary of feature_name: importance_score
        """
        if not hasattr(self.model, 'feature_importances_'):
            raise ValueError("Model doesn't support feature importance")
        
        importances = self.model.feature_importances_
        importance_dict = dict(zip(self.feature_names, importances))
        
        # Sort by importance
        sorted_importances = dict(
            sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        )
        
        logger.info(f"Top 5 features: {list(sorted_importances.items())[:5]}")
        return sorted_importances


class PropositionRanker:
    """Ranks propositions using trained ML model."""
    
    def __init__(self, db: Session, model_path: str):
        """Initialize ranker with trained model.
        
        Args:
            db: SQLAlchemy session
            model_path: Path to trained model
        """
        self.db = db
        self.trainer = MLModelTrainer(db)
        self.trainer.load_model(model_path)
        self.feature_engineer = FeatureEngineer(db)
        self.proposition_repo = PropositionRepository(db)
    
    def rank_propositions(
        self, 
        user_id: UUID, 
        propositions_ids: List[UUID],
        top_k: int = 5
    ) -> List[Tuple[UUID, float]]:
        """Rank propositions for a user.
        
        Args:
            user_id: User ID
            propositions_ids: List of proposition IDs to rank
            top_k: Return top K propositions
            
        Returns:
            List of (proposition_id, confidence_score) tuples
        """
        logger.info(f"Ranking {len(propositions_ids)} propositions for user {user_id}")
        
        # Get user features
        user_features = self.feature_engineer.engineer_all_features(user_id)
        feature_vector = np.array([user_features.get(f, 0.0) 
                                   for f in self.trainer.feature_names]).reshape(1, -1)
        
        # Get scores
        scores = self.trainer.predict(feature_vector)[0]
        
        # Create ranking with proposition scores
        rankings = []
        for prop_id in propositions_ids:
            prop = self.proposition_repo.read(prop_id)
            if prop:
                # Combine model score with proposition confidence
                combined_score = 0.6 * scores + 0.4 * prop.confidence_score
                rankings.append((prop_id, float(combined_score)))
        
        # Sort by score and return top_k
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings[:top_k]
    
    def get_ranking_explanation(self, user_id: UUID) -> Dict[str, any]:
        """Get explanation for ranking decision.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with ranking explanation
        """
        user_features = self.feature_engineer.engineer_all_features(user_id)
        importances = self.trainer.get_feature_importance()
        
        # Get top contributing features
        top_features = dict(list(importances.items())[:5])
        user_top_values = {f: user_features.get(f, 0.0) for f in top_features.keys()}
        
        return {
            "user_id": str(user_id),
            "top_features": top_features,
            "user_feature_values": user_top_values,
            "explanation": f"Ranking based on user's {', '.join(list(top_features.keys())[:3])}"
        }


class ModelVersionManager:
    """Manages model versions and persistence."""
    
    def __init__(self, db: Session, model_dir: str = "./models"):
        """Initialize version manager.
        
        Args:
            db: SQLAlchemy session
            model_dir: Directory to store models
        """
        self.db = db
        self.model_dir = model_dir
    
    def save_version(self, trainer: MLModelTrainer, metrics: Dict[str, float]) -> str:
        """Save model version with metrics.
        
        Args:
            trainer: Trained MLModelTrainer
            metrics: Model performance metrics
            
        Returns:
            Version identifier
        """
        version = trainer.save_model(f"{self.model_dir}/model_latest")
        
        # Store metrics in database
        perf = ModelPerformance(
            model_version=version,
            accuracy=metrics.get('r2', 0.0),
            precision=0.0,  # Placeholder
            recall=0.0,  # Placeholder
            f1_score=0.0,  # Placeholder
            auc_roc=metrics.get('r2', 0.0),
            total_predictions=metrics.get('test_size', 0)
        )
        self.db.add(perf)
        self.db.commit()
        
        logger.info(f"Model version {version} saved with R²={metrics.get('r2', 0):.4f}")
        return version
    
    def get_best_version(self) -> Optional[str]:
        """Get best performing model version.
        
        Returns:
            Best model version identifier
        """
        best_perf = self.db.query(ModelPerformance)\
            .order_by(ModelPerformance.auc_roc.desc())\
            .first()
        
        if best_perf:
            return best_perf.model_version
        return None
    
    def list_versions(self, limit: int = 10) -> List[Dict[str, any]]:
        """List model versions.
        
        Args:
            limit: Maximum versions to return
            
        Returns:
            List of version information
        """
        versions = self.db.query(ModelPerformance)\
            .order_by(ModelPerformance.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [{
            "version": v.model_version,
            "r2": v.auc_roc,
            "accuracy": v.accuracy,
            "created_at": v.created_at.isoformat()
        } for v in versions]
