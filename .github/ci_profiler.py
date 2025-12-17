#!/usr/bin/env python3
"""CI Profiler: Continuous profiling for performance regression detection (Level 3.1)."""
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

class CIProfiler:
    """Profile code execution and detect performance regressions."""
    
    def __init__(self):
        self.baseline_dir = Path('.metrics/profiles')
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        
    def get_baseline(self, test_name: str) -> dict:
        """Load baseline profile for comparison."""
        baseline_file = self.baseline_dir / f"{test_name}_baseline.json"
        if not baseline_file.exists():
            return {}
        
        with open(baseline_file) as f:
            return json.load(f)
    
    def detect_regressions(self, current: dict, baseline: dict) -> list:
        """Detect performance regressions vs baseline."""
        regressions = []
        
        for func, current_time in current.items():
            if func in baseline:
                baseline_time = baseline[func]
                pct_increase = ((current_time - baseline_time) / baseline_time) * 100
                
                if pct_increase > 20:  # Alert if >20% slowdown
                    regressions.append({
                        'function': func,
                        'baseline_ms': baseline_time,
                        'current_ms': current_time,
                        'increase_pct': pct_increase,
                        'severity': 'critical' if pct_increase > 50 else 'warning'
                    })
        
        return regressions
    
    def generate_pr_comment(self, regressions: list) -> str:
        """Generate GitHub PR comment with profiling results."""
        if not regressions:
            return "### ⚡ Performance: No regressions detected"
        
        comment = "### ⚠️ Performance Regressions Detected\n\n"
        comment += "| Function | Baseline | Current | Increase | Severity |\n"
        comment += "|----------|----------|---------|----------|----------|\n"
        
        for reg in regressions:
            comment += f"| `{reg['function']}` | {reg['baseline_ms']:.2f}ms | {reg['current_ms']:.2f}ms | +{reg['increase_pct']:.1f}% | {reg['severity'].upper()} |\n"
        
        comment += "\n> Run `python .github/ci_profiler.py` locally to investigate\n"
        return comment
    
    def profile_test_suite(self) -> dict:
        """Profile test execution times."""
        print("📊 Profiling test suite...")
        
        cmd = [
            "pytest", "tests/",
            "--benchmark-only",
            "--benchmark-json=.metrics/benchmark.json"
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            with open('.metrics/benchmark.json') as f:
                data = json.load(f)
            
            profile_data = {
                timestamp: datetime.utcnow().isoformat(),
                benchmarks: {}
            }
            
            for benchmark in data.get('benchmarks', []):
                profile_data['benchmarks'][benchmark['name']] = benchmark['stats']['mean']
            
            return profile_data
        except Exception as e:
            print(f"❌ Profiling failed: {e}")
            return {}
    
    def main(self):
        """Main entry point."""
        print("🔍 Level 3.1a: Continuous Profiling")
        
        # Profile current execution
        current_profile = self.profile_test_suite()
        
        if not current_profile:
            print("⚠️ No profiling data collected")
            return
        
        # Load baseline (from first run or committed to repo)
        baseline_profile = self.get_baseline('test_suite')
        
        # Detect regressions
        regressions = self.detect_regressions(
            current_profile.get('benchmarks', {}),
            baseline_profile.get('benchmarks', {})
        )
        
        # Print results
        print(f"\n✅ Profiled {len(current_profile.get('benchmarks', {}))} functions")
        
        if regressions:
            print(f"\n⚠️  Found {len(regressions)} regressions:")
            for reg in regressions:
                print(f"  - {reg['function']}: +{reg['increase_pct']:.1f}%")
            
            # Output for GitHub
            comment = self.generate_pr_comment(regressions)
            print(f"\n{comment}")
        else:
            print("\n✅ No performance regressions detected")
        
        # Save current profile as new baseline for next run
        baseline_file = self.baseline_dir / "test_suite_baseline.json"
        with open(baseline_file, 'w') as f:
            json.dump(current_profile, f, indent=2)
        
        print(f"\n💾 Baseline saved to {baseline_file}")

if __name__ == '__main__':
    profiler = CIProfiler()
    profiler.main()
