# Staging to Production Deployment Guide
## Level 3 CI/CD Intelligence System

---

## Executive Summary

This guide outlines the complete process for deploying Level 3 from the **staging** branch to **production** (main), including:
- 1-2 week calibration period
- ML model fine-tuning
- Notification system configuration
- Automated remediation setup
- Production monitoring

**Timeline**: 14-21 days from staging deployment to production release

---

## Phase 1: Staging Deployment (Days 1-2)

### 1.1 Current Status

✅ **Staging Branch Status**:
- 49 commits deployed
- level3-staging-monitor.yml workflow active
- All 5 Level 3 tools available
- Notification hub configured

### 1.2 Activate Staging Monitoring

```bash
# The workflow runs every 6 hours
# Manual trigger available via:
git checkout staging
git commit --allow-empty -m 'Trigger Level 3 monitoring'
git push origin staging
```

### 1.3 Configure Notification Channels

#### Slack Integration
```bash
# Set environment variable in GitHub Actions secrets
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### Email Integration
```bash
# Set email environment variables
NOTIFICATION_EMAIL_SENDER=your-email@gmail.com
NOTIFICATION_EMAIL_PASSWORD=your-app-password
NOTIFICATION_EMAIL_RECIPIENTS=team1@example.com,team2@example.com
```

#### Telegram Integration
```bash
# Set Telegram bot credentials
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

---

## Phase 2: Calibration Period (Days 3-14)

### 2.1 Data Collection

**Objective**: Collect baseline metrics from your typical pipeline runs

**Duration**: Minimum 10-14 pipeline runs

**What's Collected**:
- Test execution times
- Pass/fail ratios
- Coverage metrics
- Performance trends

**Monitor at**: `.github/test_data/`

### 2.2 ML Model Calibration

#### Step 1: Analyze Predictions

```python
# After 10+ runs, check prediction accuracy
python .github/ci_ml_predictor.py
# Check .github/predictions/ for results
```

#### Step 2: Adjust Risk Thresholds

Edit `.github/ci_ml_predictor.py`:

```python
def predict_failure_risk(self, current_features: Dict) -> float:
    """Calibrate these weights for your pipeline"""
    risk_score = 0.0
    
    # Adjust these thresholds based on actual data
    if current_features.get("pass_rate", 100) < 85:  # ← Your threshold
        risk_score += 0.3  # ← Your weight
    
    if current_features.get("avg_duration", 0) > 10:  # ← Your target time
        risk_score += 0.2  # ← Your weight
    
    # ... more thresholds
    return min(1.0, risk_score)
```

### 2.3 Calibration Metrics

| Metric | Target | Adjust If |
|--------|--------|----------|
| **False Positives** | < 15% | Reduce risk weights |
| **False Negatives** | < 10% | Increase risk weights |
| **Alert Accuracy** | > 85% | Fine-tune thresholds |
| **Response Time** | < 5min | Check notification delays |

### 2.4 Weekly Reviews

**Week 1 (Days 3-7)**:
- Monitor calibration reports
- Check notification delivery
- Validate risk scores
- Document adjustments

**Week 2 (Days 8-14)**:
- Verify ML accuracy
- Test notification routing
- Prepare production config
- Final approval review

---

## Phase 3: Fine-tuning (Days 15-18)

### 3.1 Model Optimization

**Review and adjust**:
- Risk score weights
- Alert thresholds
- Anomaly detection sensitivity
- Recommendation triggers

### 3.2 Notification Testing

```python
from .github.ci_notification_hub import NotificationHub

hub = NotificationHub()

# Test each channel
hub.notify(
    "Production Test",
    "Testing notification system",
    "CRITICAL"
)
```

### 3.3 Remediation Automation

Create `.github/workflows/remediation.yml`:

```yaml
name: Automated Remediation
on:
  repository_dispatch:
    types: [trigger-remediation]

jobs:
  remediate:
    runs-on: ubuntu-latest
    steps:
      # Auto-restart failed tests
      # Revert problematic commits
      # Notify teams
      # Create incident tickets
```

---

## Phase 4: Production Release (Days 19-21)

### 4.1 Pre-Release Checklist

- [ ] ML model accuracy > 85%
- [ ] All notification channels tested
- [ ] Remediation workflow ready
- [ ] Documentation complete
- [ ] Team training completed
- [ ] Runbook prepared
- [ ] Rollback plan documented

### 4.2 Merge to Production

```bash
# Create PR from staging to main
git checkout main
git pull origin main
git merge staging
git push origin main

# GitHub Actions will trigger:
# 1. optimize.yml - enhanced workflow
# 2. level3-monitoring.yml - continuous monitoring
# 3. Notifications to all channels
```

### 4.3 Production Activation

```bash
# Verify on production
git log --oneline | head -5  # See recent commits

# Check workflow
git ls-tree -r main .github/workflows/  # Confirm files

# Monitor first 24 hours
# Check GitHub Actions > Workflows
# Monitor notification channels
```

---

## Phase 5: Production Monitoring (Ongoing)

### 5.1 Daily Checks

- Pipeline success rate
- Alert accuracy
- Notification delivery
- Remediation effectiveness

### 5.2 Weekly Reviews

- Trend analysis
- Risk score validation
- Performance metrics
- Team feedback

### 5.3 Monthly Optimization

- Model retraining
- Threshold updates
- New feature requests
- Process improvements

---

## Rollback Plan

If production issues occur:

```bash
# Immediate rollback
git revert <production-commit-hash>
git push origin main

# Disable workflows
# Notify teams
# Investigate root cause
# Return to staging for fixes
```

---

## Success Metrics

| KPI | Target | Measurement |
|-----|--------|-------------|
| **Failure Detection** | 90%+ | Detected failures vs actual |
| **False Alerts** | <10% | False alarms per week |
| **Response Time** | <5min | Alert to human response |
| **System Uptime** | 99%+ | CI/CD availability |
| **User Satisfaction** | 4.5/5 | Team feedback survey |

---

## Support & Troubleshooting

**Issue**: Predictions too aggressive (too many alerts)
**Solution**: Reduce risk weights in `predict_failure_risk()`

**Issue**: Missed failures (too few alerts)  
**Solution**: Increase risk weights, lower thresholds

**Issue**: Notifications not delivering
**Solution**: Verify API keys, check logs, test each channel

**Issue**: High false positives
**Solution**: Run calibration week 2, adjust anomaly threshold

---

## Contact & Resources

- **Documentation**: See LEVEL_3_INTEGRATION_GUIDE.md
- **API Reference**: See ci_*.py files
- **Workflows**: See .github/workflows/
- **Support**: GitHub Issues

---

**Last Updated**: 2025-12-17
**Status**: Ready for Staging Deployment
**Target Production Date**: 2025-01-07
