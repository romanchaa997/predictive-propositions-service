# Predictive Propositions Service

**ML-powered microservice for generating contextual predictive propositions.** Leverages machine learning ranking models to suggest relevant user actions in real-time based on user history, context, and global patterns.

## Overview

This service provides:
- **Real-time suggestion ranking** via FastAPI/Flask REST API
- **Online ML ranking model** (logistic regression / gradient boosting) for contextual scoring
- **Offline feature engineering & candidate generation** pipeline
- **Sub-150ms latency** with caching and graceful degradation
- **Event-driven architecture** for logging impressions, clicks, and conversions
- **Monitoring & metrics** for CTR, acceptance rate, latency, coverage

## Architecture

```
┌─────────────┐
│   Frontend  │ (submit context: user_id, action type, device)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Predictive Propositions API        │
│  - Context ingestion                │
│  - Feature generation               │
│  - ML ranking (online)              │
│  - Response formatting              │
└──────┬──────────────────────────────┘
       │
       ├──────────────────┬─────────────────┐
       ▼                  ▼                 ▼
   [Cache]          [ML Model]      [Rule-based
   (user+ctx)       (Ranker)         Fallback]
       │                  │                 │
       └──────────┬───────┴─────────────────┘
                  ▼
         [Event Logger]
         (impressions,
          clicks, conversions)
                  │
                  ▼
         [Data Warehouse]
         (feature store,
          analytics)
```

### Components

#### 1. **Backend API** (`src/api/`)
- FastAPI application with endpoints:
  - `POST /suggest` → returns ranked list of propositions
  - `POST /log_event` → logs impression/click/conversion events
  - `GET /health` → service health check
- Request validation (user_id, context, limit)
- Response caching layer

#### 2. **Feature Engineering** (`src/features/`)
- User features: frequency, recency, user embedding (offline-computed)
- Context features: timestamp, device type, current action, session length
- Item features: popularity, category, embedding
- Aggregation: CTR by category, top-N patterns

#### 3. **ML Ranking Model** (`src/ml/`)
- Online ranker: logistic regression / GBDT / lightweight NN
- Candidate generation: offline top-N by category + user similarity
- Model versioning & A/B testing support
- Fallback: rule-based ranking if model unavailable

#### 4. **Data Pipeline** (`src/data/`)
- Event streaming: logs from API → data warehouse
- Feature aggregation: daily/hourly offline jobs
- Model retraining: weekly offline job with new data

#### 5. **Monitoring & Logging** (`src/monitoring/`)
- Metrics: CTR, acceptance rate, latency, error rate, coverage
- Dashboards: Grafana / Datadog integration
- Alerts: latency > 150ms, error rate > 1%, coverage < 80%

## Directory Structure

```
predictive-propositions-service/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app, routes
│   │   ├── models.py               # Request/response schemas
│   │   ├── handlers.py             # Endpoint handlers
│   │   └── middleware.py           # Caching, rate limiting
│   ├── features/
│   │   ├── __init__.py
│   │   ├── feature_store.py        # Feature caching & retrieval
│   │   ├── user_features.py        # User-level features
│   │   ├── context_features.py     # Request context features
│   │   └── item_features.py        # Candidate item features
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── ranker.py               # Ranking model wrapper
│   │   ├── candidate_gen.py        # Candidate generation logic
│   │   └── models/
│   │       └── ranker_v1.pkl       # Serialized model
│   ├── data/
│   │   ├── __init__.py
│   │   ├── event_logger.py         # Event streaming
│   │   ├── feature_aggregator.py   # Offline feature jobs
│   │   └── db_utils.py             # Data warehouse access
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── metrics.py              # Prometheus metrics
│   │   └── logger.py               # Structured logging
│   └── config.py                   # Configuration, env vars
├── ml_training/
│   ├── train.py                    # Model training script
│   ├── evaluate.py                 # Model evaluation
│   └── datasets/
│       └── README.md               # Data prep guide
├── tests/
│   ├── test_api.py
│   ├── test_ranker.py
│   ├── test_features.py
│   └── conftest.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
├── requirements.txt
├── README.md
├── .gitignore
└── .github/
    └── workflows/
        ├── test.yml                # Unit & integration tests
        ├── deploy.yml              # CD pipeline
        └── model_retrain.yml       # Weekly model retraining
```

## Tech Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn
- **ML:** scikit-learn / XGBoost / LightGBM
- **Data:** PostgreSQL / DuckDB (feature store), Kafka (event streaming)
- **Caching:** Redis
- **Monitoring:** Prometheus, Grafana
- **Deployment:** Docker, Kubernetes
- **Testing:** pytest, pytest-cov

## Setup & Installation

### Prerequisites
- Python 3.10+
- Docker & Docker Compose (optional)
- Redis (optional, for caching)

### Local Development

```bash
# Clone repo
git clone https://github.com/romanchaa997/predictive-propositions-service.git
cd predictive-propositions-service

# Create venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up env vars
cp .env.example .env
# Edit .env with your config

# Run tests
pytest tests/ -v

# Start API locally
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000`

API docs (Swagger): `http://localhost:8000/docs`

## Usage

### Suggest Propositions

```bash
curl -X POST http://localhost:8000/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "context": "search_query",
    "context_type": "search",
    "limit": 5,
    "device": "mobile"
  }'
```

**Response:**
```json
{
  "propositions": [
    {
      "id": "prop_456",
      "title": "Popular Search",
      "confidence": 0.87,
      "reason": "trending + user_interest"
    },
    ...
  ],
  "served_by": "ml_ranker",
  "latency_ms": 42
}
```

### Log Event

```bash
curl -X POST http://localhost:8000/log_event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "click",
    "user_id": "user_123",
    "proposition_id": "prop_456",
    "timestamp": "2025-12-13T22:00:00Z"
  }'
```

## Implementation Roadmap

### Phase 1: Skeleton & Rule-Based (Week 1-2)
- [ ] Task 1: Set up FastAPI project structure & basic health endpoint
- [ ] Task 2: Design & implement request/response schemas
- [ ] Task 3: Implement rule-based ranking (frequency + popularity)
- [ ] Task 4: Add event logging (in-memory for now)
- [ ] Task 5: Deploy to staging, basic E2E test

### Phase 2: Data & Feature Engineering (Week 3-4)
- [ ] Task 6: Set up PostgreSQL / DuckDB feature store
- [ ] Task 7: Build user feature pipeline (frequency, recency, embeddings)
- [ ] Task 8: Build context & item feature extractors
- [ ] Task 9: Data pipeline for aggregating CTR, popularity by category
- [ ] Task 10: Create feature store mock for offline testing

### Phase 3: ML Model & Online Ranking (Week 5-6)
- [ ] Task 11: Prepare dataset from event logs (user-item pairs + labels)
- [ ] Task 12: Train baseline logistic regression ranker
- [ ] Task 13: Evaluate model: AUC, NDCG, offline metrics
- [ ] Task 14: Integrate ML ranker into API (feature generation → model inference)
- [ ] Task 15: Add model versioning & A/B test support

### Phase 4: Production Hardening (Week 7-8)
- [ ] Task 16: Add response caching (Redis)
- [ ] Task 17: Implement graceful degradation (rule-based fallback)
- [ ] Task 18: Add metrics collection (Prometheus)
- [ ] Task 19: Set up Kubernetes deployment manifests
- [ ] Task 20: E2E testing, load testing (latency SLA)

### Phase 5: Monitoring & Iteration (Week 9+)
- [ ] Task 21: Grafana dashboards for CTR, acceptance rate, latency
- [ ] Task 22: Set up alerts for anomalies
- [ ] Task 23: Automated weekly model retraining job
- [ ] Task 24: A/B test framework & experiment tracking
- [ ] Task 25: Documentation & runbook

## Key Metrics

| Metric | Target | Definition |
|--------|--------|------------|
| **Latency (p99)** | <150ms | Time from request to response |
| **CTR** | >5% | % of shown propositions clicked |
| **Acceptance Rate** | >30% | % of users who act on suggestion |
| **Coverage** | >90% | % of requests with propositions |
| **Error Rate** | <1% | Failed requests / total |
| **Model Quality (AUC)** | >0.75 | Offline ranking quality |

## Contributing

1. Create a feature branch: `git checkout -b feature/xyz`
2. Commit changes: `git commit -m "Add feature xyz"`
3. Push to branch: `git push origin feature/xyz`
4. Open a Pull Request

## License

MIT License (see LICENSE file)

## Contact

Maintainer: [@romanchaa997](https://github.com/romanchaa997)

---

**Status:** 🚧 Early-stage PoC, rapid iteration expected.
