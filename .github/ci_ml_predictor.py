#!/usr/bin/env python3
"""
Level 3.3: CI ML Predictor

Machine Learning model for predicting test failures and performance issues
based on historical CI pipeline data.

Features:
- Failure prediction
- Performance regression detection
- Anomaly detection
- Risk scoring
- Recommendations generation
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pickle
import warnings

warnings.filterwarnings('ignore')

try:
    import numpy as np
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class CIMLPredictor:
    """ML-based CI/CD pipeline predictor and anomaly detector."""

    def __init__(self, data_dir: str = ".github/test_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.scaler = None
        self.anomaly_detector = None

    def load_historical_data(self) -> List[Dict[str, Any]]:
        """Load historical test data."""
        data = []
        if self.data_dir.exists():
            for file in sorted(self.data_dir.glob("test_data_*.json")):
                try:
                    with open(file) as f:
                        data.append(json.load(f))
                except Exception as e:
                    print(f"Warning: Could not load {file}: {e}")
        return data

    def extract_features(self, test_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract ML features from test data."""
        summary = test_data.get("summary", {})
        features = {
            "pass_rate": summary.get("pass_rate", 100),
            "avg_duration": summary.get("avg_test_duration", 0),
            "total_tests": summary.get("total_tests", 0),
            "failed_tests": summary.get("failed", 0),
            "skipped_tests": summary.get("skipped", 0),
        }
        return features

    def detect_anomalies(self, features_list: List[Dict]) -> List[Dict]:
        """Detect anomalies in test data using Isolation Forest."""
        if not SKLEARN_AVAILABLE or len(features_list) < 2:
            return []

        try:
            X = np.array([[f.get("pass_rate"), f.get("avg_duration")] 
                         for f in features_list])
            
            self.anomaly_detector = IsolationForest(
                contamination=0.1, random_state=42
            )
            predictions = self.anomaly_detector.fit_predict(X)
            
            anomalies = []
            for idx, pred in enumerate(predictions):
                if pred == -1:
                    anomalies.append({
                        "index": idx,
                        "features": features_list[idx],
                        "type": "performance_anomaly"
                    })
            return anomalies
        except Exception as e:
            print(f"Anomaly detection error: {e}")
            return []

    def predict_failure_risk(self, current_features: Dict) -> float:
        """Predict risk of test failure (0-1 scale)."""
        risk_score = 0.0
        
        # Rule-based heuristics for failure prediction
        if current_features.get("pass_rate", 100) < 85:
            risk_score += 0.3
        if current_features.get("avg_duration", 0) > 10:
            risk_score += 0.2
        if current_features.get("failed_tests", 0) > 0:
            risk_score += 0.3
        if current_features.get("skipped_tests", 0) > 0:
            risk_score += 0.1
            
        return min(1.0, risk_score)

    def generate_recommendations(self, 
                                risk_score: float,
                                features: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        if risk_score > 0.7:
            recommendations.append("CRITICAL: Investigate test failures immediately")
        elif risk_score > 0.5:
            recommendations.append("WARNING: Performance degradation detected")
        
        if features.get("avg_duration", 0) > 10:
            recommendations.append("Optimize slow tests - consider parallelization")
        
        if features.get("pass_rate", 100) < 85:
            recommendations.append("Review recent commits for regression")
            
        if not recommendations:
            recommendations.append("Pipeline health is good - no action needed")
            
        return recommendations

    def predict(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions on current CI data."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0.0,
            "anomalies": [],
            "recommendations": []
        }
        
        # Load historical data
        historical = self.load_historical_data()
        all_features = [self.extract_features(d) for d in historical]
        
        # Extract current features
        current_features = self.extract_features(current_data)
        
        # Detect anomalies
        if all_features:
            result["anomalies"] = self.detect_anomalies(all_features)
        
        # Predict failure risk
        risk_score = self.predict_failure_risk(current_features)
        result["risk_score"] = risk_score
        
        # Generate recommendations
        result["recommendations"] = self.generate_recommendations(
            risk_score, current_features
        )
        
        return result

    def save_predictions(self, predictions: Dict[str, Any]) -> str:
        """Save predictions to file."""
        output_dir = self.data_dir.parent / "predictions"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().isoformat().replace(':', '-')
        filename = output_dir / f"prediction_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(predictions, f, indent=2)
        
        return str(filename)


if __name__ == "__main__":
    predictor = CIMLPredictor()
    print("\u2728 ML Predictor initialized (Level 3.3)")
    print("\u2705 Ready for failure prediction and anomaly detection")
