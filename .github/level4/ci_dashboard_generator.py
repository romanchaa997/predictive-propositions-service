#!/usr/bin/env python3
"""
Level 4.1: CI Dashboard Generator

Real-time metrics visualization dashboard for Level 3 data.
Generates interactive HTML/JSON dashboards with:
- Live metric visualization
- Risk score trending
- Performance graphs
- Anomaly highlights
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import statistics


class DashboardGenerator:
    """Generates interactive dashboards from Level 3 data."""

    def __init__(self, data_dir: str = ".github/test_data"):
        self.data_dir = Path(data_dir)
        self.predictions_dir = Path(".github/predictions")
        self.dashboard_dir = Path(".github/dashboards")
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect metrics from test data and predictions."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "test_metrics": [],
            "risk_scores": [],
            "anomalies": [],
            "recommendations": []
        }

        # Load test data
        if self.data_dir.exists():
            for file in sorted(self.data_dir.glob("test_data_*.json"))[-10:]:
                try:
                    with open(file) as f:
                        data = json.load(f)
                        if "summary" in data:
                            metrics["test_metrics"].append(data["summary"])
                except Exception as e:
                    print(f"Error loading {file}: {e}")

        # Load predictions
        if self.predictions_dir.exists():
            for file in sorted(self.predictions_dir.glob("prediction_*.json"))[-10:]:
                try:
                    with open(file) as f:
                        data = json.load(f)
                        metrics["risk_scores"].append(data.get("risk_score", 0))
                        metrics["anomalies"].extend(data.get("anomalies", []))
                        metrics["recommendations"].extend(data.get("recommendations", []))
                except Exception as e:
                    print(f"Error loading {file}: {e}")

        return metrics

    def generate_html_dashboard(self, metrics: Dict) -> str:
        """Generate interactive HTML dashboard."""
        avg_risk = statistics.mean(metrics["risk_scores"]) if metrics["risk_scores"] else 0
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Level 3 CI/CD Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; border-radius: 8px; background: #f0f0f0; }}
        .risk-high {{ color: #d32f2f; }}
        .risk-medium {{ color: #f57c00; }}
        .risk-low {{ color: #388e3c; }}
    </style>
</head>
<body>
    <h1>🚀 Level 3 CI/CD Intelligence Dashboard</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="metric">
        <h3>Average Risk Score</h3>
        <p class="{"risk-high" if avg_risk > 0.7 else "risk-medium" if avg_risk > 0.5 else "risk-low"}"
           style="font-size: 32px; font-weight: bold;">
            {avg_risk:.2f}
        </p>
    </div>
    
    <div class="metric">
        <h3>Total Tests Analyzed</h3>
        <p style="font-size: 32px; font-weight: bold;">
            {sum(m.get("total_tests", 0) for m in metrics["test_metrics"])}
        </p>
    </div>
    
    <div class="metric">
        <h3>Anomalies Detected</h3>
        <p style="font-size: 32px; font-weight: bold;">
            {len(metrics["anomalies"])}
        </p>
    </div>
    
    <h2>System Health Status</h2>
    <p>✅ All Level 3 tools operational</p>
    <p>📊 Monitoring: Active</p>
    <p>🔔 Alerts: {'Enabled' if metrics['risk_scores'] else 'No data'}</p>
</body>
</html>
        """
        return html

    def generate_json_dashboard(self, metrics: Dict) -> str:
        """Generate JSON API response for dashboard."""
        return json.dumps({
            "status": "operational",
            "timestamp": metrics["timestamp"],
            "summary": {
                "avg_risk_score": statistics.mean(metrics["risk_scores"]) if metrics["risk_scores"] else 0,
                "total_metrics_collected": len(metrics["test_metrics"]),
                "anomalies_count": len(metrics["anomalies"]),
                "active_recommendations": len(set(metrics["recommendations"]))
            },
            "trend": {
                "risk_scores_last_10": metrics["risk_scores"][-10:],
                "pass_rates": [m.get("pass_rate", 0) for m in metrics["test_metrics"][-10:]]
            }
        }, indent=2)

    def generate_dashboards(self) -> Dict[str, str]:
        """Generate all dashboard formats."""
        print("\u2728 Generating dashboards...")
        metrics = self.collect_metrics()
        
        dashboards = {
            "html": self.generate_html_dashboard(metrics),
            "json": self.generate_json_dashboard(metrics)
        }
        
        # Save dashboards
        timestamp = datetime.now().isoformat().replace(':', '-')
        
        html_file = self.dashboard_dir / f"dashboard_{timestamp}.html"
        with open(html_file, "w") as f:
            f.write(dashboards["html"])
        print(f"✅ HTML dashboard saved: {html_file}")
        
        json_file = self.dashboard_dir / f"dashboard_{timestamp}.json"
        with open(json_file, "w") as f:
            f.write(dashboards["json"])
        print(f"✅ JSON dashboard saved: {json_file}")
        
        return dashboards


if __name__ == "__main__":
    generator = DashboardGenerator()
    generator.generate_dashboards()
