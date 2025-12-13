#!/usr/bin/env python3
"""ML Training script for Predictive Propositions Ranker"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, ndcg_score, precision_recall_curve
import joblib
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_synthetic_data(n_samples=5000):
    """Generate synthetic training data (Phase 2-3)"""
    np.random.seed(42)
    
    # Features: user_id, context, frequency, recency, popularity, item_embedding (5D)
    X = np.random.randn(n_samples, 10)
    
    # Labels: click (1) vs no click (0) - binary classification
    # More likely to click if user_frequency + item_popularity is high
    y = (X[:, 2] + X[:, 4] > 0).astype(int)  # 50% positive class
    
    # Add some noise
    noise_idx = np.random.choice(n_samples, size=int(0.1 * n_samples), replace=False)
    y[noise_idx] = 1 - y[noise_idx]
    
    return X, y

def train_ranker(X_train, y_train, X_val, y_val):
    """Train logistic regression ranker (Phase 3)"""
    logger.info("Training logistic regression ranker...")
    
    # Feature scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # Train model
    model = LogisticRegression(
        max_iter=1000,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    train_auc = roc_auc_score(y_train, model.predict_proba(X_train_scaled)[:, 1])
    val_auc = roc_auc_score(y_val, model.predict_proba(X_val_scaled)[:, 1])
    
    logger.info(f"Train AUC: {train_auc:.4f}, Val AUC: {val_auc:.4f}")
    
    return model, scaler, {'train_auc': train_auc, 'val_auc': val_auc}

def main():
    """Main training pipeline"""
    logger.info("Starting ML training pipeline...")
    
    # Generate data
    X, y = generate_synthetic_data(n_samples=5000)
    
    # Split: 80% train, 10% val, 10% test
    split_idx1 = int(0.8 * len(X))
    split_idx2 = int(0.9 * len(X))
    
    X_train, y_train = X[:split_idx1], y[:split_idx1]
    X_val, y_val = X[split_idx1:split_idx2], y[split_idx1:split_idx2]
    X_test, y_test = X[split_idx2:], y[split_idx2:]
    
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Train model
    model, scaler, metrics = train_ranker(X_train, y_train, X_val, y_val)
    
    # Test evaluation
    X_test_scaled = scaler.transform(X_test)
    test_auc = roc_auc_score(y_test, model.predict_proba(X_test_scaled)[:, 1])
    logger.info(f"Test AUC: {test_auc:.4f}")
    
    # Save model
    model_path = Path('src/ml/models/ranker_v1.pkl')
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Save scaler
    scaler_path = Path('src/ml/models/scaler_v1.pkl')
    joblib.dump(scaler, scaler_path)
    logger.info(f"Scaler saved to {scaler_path}")
    
    logger.info("Training completed!")
    return metrics

if __name__ == '__main__':
    metrics = main()
