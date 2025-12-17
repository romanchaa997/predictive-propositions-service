#!/usr/bin/env python3
"""CI Metrics Analyzer: Auto-generate optimization recommendations."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class CIMetricsAnalyzer:
    """Analyze CI/CD performance and suggest optimizations."""
    
    def __init__(self):
        self.metrics = {}
        self.recommendations = []
        self.baseline_file = Path('.metrics/baseline.json')
        
    def analyze_test_duration(self, duration_sec: float) -> List[str]:
        """Suggest optimizations based on test duration."""
        recs = []
        if duration_sec > 30:
            recs.append('Level 2.1: Test filtering - skip unrelated tests')
            recs.append('Level 3.1: ML test prediction - reduce suite by 30-50%')
        if duration_sec > 60:
            recs.append('Level 2.4: Test sharding - split across 4 runners')
            recs.append('Level 3.1: Implement smart test selection')
        return recs
    
    def analyze_docker_build(self, duration_sec: float) -> List[str]:
        """Suggest Docker optimizations."""
        recs = []
        if duration_sec > 120:
            recs.append('Level 1.3: Multi-stage Dockerfile (20-30% faster)')
            recs.append('Level 1.3: Add .dockerignore (reduce context)')
            recs.append('Level 3.4: Distributed caching system')
        elif duration_sec > 60:
            recs.append('Level 1.3: Reorder Dockerfile (system deps -> pip -> code)')
            recs.append('Level 2.2: Skip Docker on feature branches')
        return recs
    
    def analyze_lint_duration(self, duration_sec: float) -> List[str]:
        """Suggest linting optimizations."""
        recs = []
        if duration_sec > 10:
            recs.append('Level 1.4: Cache linting results (skip if no code changes)')
            recs.append('Level 1.4: Reduce complexity threshold 10 -> 12')
        return recs
    
    def analyze_cache_effectiveness(self, hit_rate: float) -> List[str]:
        """Suggest caching improvements."""
        recs = []
        if hit_rate < 0.6:
            recs.append('Level 1.2: Optimize pip cache key (include hash)')
            recs.append('Level 3.4: Implement S3/MinIO global cache backend')
        return recs
    
    def analyze_flakiness(self, failure_rate: float) -> List[str]:
        """Detect and suggest fixes for flaky tests."""
        recs = []
        if failure_rate > 0.1:
            recs.append('Level 1.2: Add pytest-timeout to prevent hangs')
            recs.append('Level 1.2: Mark slow/flaky tests with @pytest.mark.flaky')
            recs.append('Level 2.3: Implement performance benchmarking')
        return recs
    
    def generate_report(self, job_metrics: Dict) -> Dict:
        """Generate comprehensive optimization report."""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': job_metrics,
            'recommendations': [],
            'priority': []
        }
        
        # Analyze each metric
        if 'test_duration_sec' in job_metrics:
            report['recommendations'].extend(
                self.analyze_test_duration(job_metrics['test_duration_sec'])
            )
        
        if 'docker_duration_sec' in job_metrics:
            report['recommendations'].extend(
                self.analyze_docker_build(job_metrics['docker_duration_sec'])
            )
        
        if 'lint_duration_sec' in job_metrics:
            report['recommendations'].extend(
                self.analyze_lint_duration(job_metrics['lint_duration_sec'])
            )
        
        if 'cache_hit_rate' in job_metrics:
            report['recommendations'].extend(
                self.analyze_cache_effectiveness(job_metrics['cache_hit_rate'])
            )
        
        if 'test_flakiness_rate' in job_metrics:
            report['recommendations'].extend(
                self.analyze_flakiness(job_metrics['test_flakiness_rate'])
            )
        
        # Deduplicate & prioritize
        report['recommendations'] = list(set(report['recommendations']))
        report['priority'] = self._prioritize(report['recommendations'])
        
        return report
    
    def _prioritize(self, recommendations: List[str]) -> List[str]:
        """Sort recommendations by level and impact."""
        level_order = {'Level 1': 0, 'Level 2': 1, 'Level 3': 2, 'Level 4': 3}
        return sorted(
            recommendations,
            key=lambda x: level_order.get(
                [k for k in level_order if k in x][0] if any(k in x for k in level_order) else 'Level 4',
                999
            )
        )
    
    def compare_with_baseline(self, current_metrics: Dict) -> Dict:
        """Compare against baseline and detect regressions."""
        if not self.baseline_file.exists():
            return {'status': 'no_baseline', 'changes': {}}
        
        with open(self.baseline_file) as f:
            baseline = json.load(f)
        
        changes = {}
        for key, current_val in current_metrics.items():
            if key in baseline:
                baseline_val = baseline[key]
                pct_change = ((current_val - baseline_val) / baseline_val * 100) if baseline_val != 0 else 0
                if abs(pct_change) > 5:  # Flag >5% change
                    changes[key] = {
                        'baseline': baseline_val,
                        'current': current_val,
                        'change_pct': pct_change,
                        'alert': 'regression' if pct_change > 0 else 'improvement'
                    }
        
        return {'status': 'compared', 'changes': changes}
    
    def export_pr_comment(self, report: Dict, comparison: Dict) -> str:
        """Generate GitHub PR comment with findings."""
        comment = '### 🚀 CI Optimization Report\n\n'
        
        # Current metrics
        comment += '#### Current Metrics\n'
        for metric, value in report['metrics'].items():
            comment += f'- **{metric}**: {value}\n'
        
        # Comparisons
        if comparison['changes']:
            comment += '\n#### Performance Changes\n'
            for metric, change in comparison['changes'].items():
                emoji = '\u26a0\ufe0f' if change['alert'] == 'regression' else '\u2705'
                comment += f'{emoji} **{metric}**: {change["change_pct"]:.1f}% ({change["baseline"]} -> {change["current"]})\n'
        
        # Top recommendations
        if report['priority']:
            comment += '\n#### Top Recommendations\n'
            for i, rec in enumerate(report['priority'][:5], 1):
                comment += f'{i}. {rec}\n'
        
        comment += '\n> See OPTIMIZATION_RECOMMENDATIONS.md for full roadmap'
        return comment


if __name__ == '__main__':
    analyzer = CIMetricsAnalyzer()
    
    # Example metrics from GitHub Actions
    example_metrics = {
        'test_duration_sec': float(os.getenv('TEST_DURATION', '45')),
        'docker_duration_sec': float(os.getenv('DOCKER_DURATION', '90')),
        'lint_duration_sec': float(os.getenv('LINT_DURATION', '8')),
        'cache_hit_rate': float(os.getenv('CACHE_HIT_RATE', '0.65')),
        'test_flakiness_rate': float(os.getenv('TEST_FLAKINESS', '0.05')),
    }
    
    report = analyzer.generate_report(example_metrics)
    comparison = analyzer.compare_with_baseline(example_metrics)
    comment = analyzer.export_pr_comment(report, comparison)
    
    print(comment)
    
    # Save report
    os.makedirs('.metrics', exist_ok=True)
    with open('.metrics/latest_report.json', 'w') as f:
        json.dump({'report': report, 'comparison': comparison}, f, indent=2)
