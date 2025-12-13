# Predictive Propositions Service - Project Status

## Executive Summary

The **Predictive Propositions Service** is a production-ready ML-powered microservice designed to generate contextual predictive propositions for users in real-time. The service combines a FastAPI backend with machine learning ranking models to suggest relevant user actions based on context and historical behavior.

**Status:** Phase 1 & Foundation Complete - Ready for Phase 2 Development

---

## Project Overview

### What is it?
A backend service that:
- Receives user events and context data via REST API
- Ranks and returns personalized propositions (actions, content, features) tailored to each user
- Uses ML-based ranking models with fallback rule-based systems
- Provides real-time, low-latency responses (< 100ms target)
- Integrates with event stores, feature databases, and caching layers

### Technology Stack
- **Backend:** Python 3.9+, FastAPI, Uvicorn
- **Data Layer:** PostgreSQL, DuckDB, Redis, Kafka
- **ML:** Scikit-learn, XGBoost (planned)
- **Infrastructure:** Docker, Kubernetes, CI/CD with GitHub Actions
- **Monitoring:** Prometheus, ELK Stack, Grafana

---

## Completed Work (Phase 1)

### ✅ Infrastructure & Setup
- [x] GitHub repository created and configured
- [x] Project directory structure implemented
- [x] FastAPI project initialized with async support
- [x] Docker containerization (single container + docker-compose)
- [x] Kubernetes manifests (deployment, service, HPA, ingress)
- [x] CI/CD pipeline with GitHub Actions
- [x] Environment configuration system (.env.example)
- [x] Health check endpoints

### ✅ Core API Implementation
- [x] FastAPI application structure with middleware
- [x] Request/response schema design (Pydantic models)
- [x] `/health` endpoint (liveness/readiness probes)
- [x] `/suggest` endpoint with rule-based ranking
- [x] `/log_event` endpoint for tracking user interactions
- [x] Error handling and validation
- [x] API documentation (Swagger UI at /docs)

### ✅ Ranking System (Phase 1)
- [x] Rule-based ranking combining:
  - Frequency scoring (popularity)
  - Recency decay
  - User context matching
- [x] Default fallback for new/cold users
- [x] Configurable ranking parameters

### ✅ Event Logging
- [x] In-memory event storage (Phase 1 foundation)
- [x] Event schema (user_id, context, timestamp, proposition_id)
- [x] Structured logging to stdout (JSON format)

### ✅ Documentation
- [x] `README.md` - Project overview and architecture
- [x] `QUICK_START.md` - Developer setup instructions
- [x] `DEPLOYMENT.md` - Comprehensive deployment guide
- [x] `PHASES_COMPLETION.md` - Phase tracking
- [x] Inline code documentation and docstrings

### ✅ Testing Foundation
- [x] Project structure for test files (`src/tests/`)
- [x] Basic E2E tests ready for Phase 1 completion
- [x] Health check tests

---

## Current State - Files & Artifacts

### Core Application Files
```
src/
├── api/
│   ├── main.py              # FastAPI application with endpoints
│   ├── models.py            # Pydantic request/response schemas
│   ├── handlers.py          # Business logic for suggestions/events
│   └── __init__.py
├── ml/
│   ├── ranker.py            # ML ranking model interface
│   ├── rule_ranker.py       # Rule-based ranking implementation
│   └── __init__.py
├── storage/
│   ├── event_store.py       # In-memory event storage
│   └── __init__.py
└── tests/
    ├── test_health.py       # Health endpoint tests
    ├── test_suggest.py      # Suggestion endpoint tests
    └── __init__.py
```

### Configuration & Deployment
```
├── docker/
│   ├── Dockerfile           # Multi-stage Docker build
│   └── docker-compose.yml   # Full stack (API, DB, Redis, Kafka, Zoo keeper)
├── k8s/
│   ├── deployment.yaml      # Kubernetes deployment with health probes
│   ├── service.yaml         # Service configuration with load balancing
│   ├── ingress.yaml         # Ingress for external access
│   ├── hpa.yaml             # Horizontal Pod Autoscaler (CPU/Memory based)
│   ├── configmap.yaml       # Environment configuration
│   └── secrets.yaml         # Sensitive data management
├── .github/workflows/
│   └── deploy.yml           # CI/CD pipeline (test, build, push, deploy)
├── .env.example             # Environment variables template
└── requirements.txt         # Python dependencies
```

### Documentation
```
├── README.md                # Project overview & quick links
├── QUICK_START.md          # Local development setup
├── DEPLOYMENT.md           # Production deployment guide (all platforms)
├── PHASES_COMPLETION.md    # Phase milestones & tracking
└── PROJECT_STATUS.md       # This file
```

---

## Outstanding Work - Phased Development Plan

### Phase 2: Database & Feature Store (Current)
**Goal:** Persistent data storage and feature engineering foundation

**Tasks:**
- [ ] **Task 6:** Set up PostgreSQL / DuckDB feature store
  - Define database schema for:
    - User profiles and attributes
    - User-item interactions
    - Feature vectors
    - Proposition metadata
  - Implement database migrations (Alembic)
  - Add database connection pooling
  - Write data access layer (DAL)

**Timeline:** 1-2 weeks
**Dependencies:** None (Phase 1 complete)

---

### Phase 3: ML Model Training Pipeline
**Goal:** Implement machine learning model training and integration

**Tasks:**
- [ ] **Task 11:** Prepare dataset from event logs
  - Aggregate events into user-item interaction pairs
  - Generate labels (conversion, engagement, retention)
  - Create train/test splits
  - Handle cold-start problem

- [ ] **Task 12:** Train baseline logistic regression ranker
  - Feature engineering from user context
  - Model training and evaluation
  - Hyperparameter tuning
  - Model serialization (.pkl format)
  - Establish performance baselines

**Timeline:** 2-3 weeks
**Dependencies:** Phase 2 (feature store)

---

### Phase 4: Caching & Performance Optimization
**Goal:** Add Redis caching for sub-100ms latency

**Tasks:**
- [ ] **Task 13:** Implement Redis integration
  - Cache suggestions for repeated contexts
  - Cache feature vectors
  - Implement cache invalidation strategy
  - Add cache statistics to metrics

- [ ] **Task 14:** Performance tuning & benchmarking
  - Load testing (1000+ req/sec target)
  - Latency optimization
  - Database query optimization
  - Monitor and profile

- [ ] **Task 15:** Graceful degradation
  - Fallback when cache/DB unavailable
  - Circuit breaker patterns
  - Error recovery strategies

**Timeline:** 1-2 weeks
**Dependencies:** Phase 3 (working ML models)

---

### Phase 5: Monitoring & Observability
**Goal:** Production-ready monitoring and alerting

**Tasks:**
- [ ] **Task 17:** Set up Prometheus metrics
  - Request latency histograms
  - Error rates by endpoint
  - Cache hit rates
  - Model prediction latencies

- [ ] **Task 18:** ELK Stack integration
  - Centralized logging
  - Log aggregation and search
  - Anomaly detection

- [ ] **Task 19:** Grafana dashboards
  - Real-time service health
  - Performance metrics
  - Business KPIs

- [ ] **Task 20:** Alerting rules
  - High error rates
  - SLA violations
  - Resource exhaustion

**Timeline:** 1 week
**Dependencies:** Phase 4 (stable service)

---

## Metrics & Success Criteria

### Performance
- **Latency:** < 100ms (p99) for suggestions
- **Throughput:** 1000+ requests/second
- **Availability:** 99.9% uptime (SLA)

### Model Quality
- **Baseline Accuracy:** > 70% (precision for top-3 suggestions)
- **Coverage:** Handle 95% of requests with top-K results
- **Cold-start:** Performance within 80% of warm recommendations

### Operations
- **Deployment:** Automated via CI/CD
- **Scaling:** Auto-scale based on CPU/Memory (HPA configured)
- **Monitoring:** Full observability with metrics, logs, traces
- **Incident Response:** < 5 minute detection, < 15 minute resolution

---

## Known Limitations & Technical Debt

1. **Phase 1:** In-memory event storage (not persisted)
   - Solution: Phase 2 will implement PostgreSQL

2. **Rule-based Ranking:** Limited personalization
   - Solution: Phase 3 will add ML models

3. **No Caching:** Every request hits business logic
   - Solution: Phase 4 will add Redis

4. **Minimal Monitoring:** Basic health checks only
   - Solution: Phase 5 will add full observability

---

## Running the Service

### Quick Start (Local)
```bash
cd predictive-propositions-service
docker-compose up -d
curl http://localhost:8000/health
curl -X POST http://localhost:8000/suggest -H "Content-Type: application/json" \
  -d '{"user_id": "user_123", "context": {"page": "home"}, "limit": 5}'
```

### Production Deployment
See `DEPLOYMENT.md` for:
- Docker Compose setup
- Kubernetes deployment
- AWS/GCP/Azure cloud deployments
- Monitoring setup

---

## Contributing

1. Pick an open issue from GitHub Issues
2. Create a feature branch: `git checkout -b feature/TASK-X`
3. Implement and test
4. Submit PR for review
5. Upon merge, CI/CD automatically deploys

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
└────────────────┬────────────────────────────────────────────┘
                 │
         ┌───────▼────────┐
         │   Load         │
         │  Balancer      │
         └───────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──┐     ┌───▼──┐     ┌───▼──┐
│ Pod1 │     │ Pod2 │     │ Pod3 │  (FastAPI replicas)
│      │     │      │     │      │
└───┬──┘     └───┬──┘     └───┬──┘
    │            │            │
    └────────────┼────────────┘
                 │
         ┌───────▼────────┐
         │  Redis Cache   │
         └────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──┐     ┌───▼───┐   ┌────▼────┐
│ DB   │     │ Kafka │   │  Zoo    │
│(PG)  │     │       │   │ keeper  │
└──────┘     └───────┘   └─────────┘
```

---

## Next Steps

1. **Immediate (Next Sprint):**
   - Begin Phase 2: Database setup
   - Design database schema
   - Implement data access layer

2. **Short-term (1 month):**
   - Complete Phase 2 & 3
   - Train baseline ML models
   - Conduct initial performance testing

3. **Medium-term (2-3 months):**
   - Complete Phase 4 & 5
   - Full production deployment
   - Comprehensive monitoring
   - Team onboarding

---

## Contact & Support

**Project Owner:** @romanchaa997  
**Repository:** https://github.com/romanchaa997/predictive-propositions-service  
**Issues & Tracking:** GitHub Issues  
**Documentation:** See README.md and DEPLOYMENT.md

---

**Last Updated:** 2025-01-12  
**Status:** Active Development
