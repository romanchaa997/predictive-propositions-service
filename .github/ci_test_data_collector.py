#!/usr/bin/env python3
"""
Level 3.2: CI Test Data Collector

Collects test execution data (timing, results, coverage) from CI pipeline
and stores it for analysis and ML model training.

Features:
- Test result aggregation
- Execution timing collection
- Coverage metrics extraction
- Data persistence to JSON
- Benchmark comparison
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import subprocess


class TestDataCollector:
    """Collects and aggregates test execution data."""

    def __init__(self, output_dir: str = ".github/test_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().isoformat()
        self.data = {"timestamp": self.timestamp, "tests": [], "summary": {}}

    def collect_test_metrics(self) -> Dict[str, Any]:
        """Collect test execution metrics."""
        try:
            result = subprocess.run(
                ["pytest", "--json-report", "--json-report-file=.pytest_json_report"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if os.path.exists(".pytest_json_report"):
                with open(".pytest_json_report") as f:
                    pytest_data = json.load(f)
                return pytest_data
        except Exception as e:
            print(f"\u274c Error collecting test metrics: {e}")
        return {}

    def collect_coverage_metrics(self) -> Dict[str, Any]:
        """Collect code coverage metrics."""
        try:
            result = subprocess.run(
                ["coverage", "report", "--json"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            print(f"\u274c Error collecting coverage: {e}")
        return {}

    def extract_test_results(self, metrics: Dict[str, Any]) -> List[Dict]:
        """Extract individual test results."""
        tests = []
        if "tests" in metrics:
            for test in metrics["tests"]:
                tests.append(
                    {
                        "name": test.get("nodeid"),
                        "duration": test.get("duration", 0),
                        "outcome": test.get("outcome"),
                        "markers": test.get("markers", []),
                    }
                )
        return tests

    def generate_summary(self) -> Dict[str, Any]:
        """Generate data summary."""
        total_tests = len(self.data["tests"])
        passed = sum(1 for t in self.data["tests"] if t.get("outcome") == "passed")
        failed = sum(1 for t in self.data["tests"] if t.get("outcome") == "failed")
        skipped = sum(1 for t in self.data["tests"] if t.get("outcome") == "skipped")
        total_duration = sum(t.get("duration", 0) for t in self.data["tests"])

        return {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration,
            "avg_test_duration": (total_duration / total_tests) if total_tests > 0 else 0,
        }

    def save_data(self) -> str:
        """Save collected data to file."""
        self.data["summary"] = self.generate_summary()
        filename = self.output_dir / f"test_data_{self.timestamp.replace(':', '-')}.json"
        with open(filename, "w") as f:
            json.dump(self.data, f, indent=2)
        return str(filename)

    def collect_all(self) -> Dict[str, Any]:
        """Collect all test data."""
        print("\u2728 Collecting test execution data...")
        metrics = self.collect_test_metrics()
        self.data["tests"] = self.extract_test_results(metrics)
        coverage = self.collect_coverage_metrics()
        self.data["coverage"] = coverage
        filename = self.save_data()
        print(f"\u2705 Test data saved to {filename}")
        return self.data


if __name__ == "__main__":
    collector = TestDataCollector()
    data = collector.collect_all()
    print(json.dumps(data["summary"], indent=2))
