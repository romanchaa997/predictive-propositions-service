# 🚀 Quick Start Guide - Predictive Propositions Service

**Get the service running in 5 minutes!**

---

## Prerequisites

- Docker & Docker Compose installed
- Git installed
- ~2GB free disk space
- Ports available: 8000 (API), 5432 (PostgreSQL), 6379 (Redis), 9092 (Kafka), 2181 (Zookeeper)

---

## Step 1: Clone Repository

```bash
git clone https://github.com/romanchaa997/predictive-propositions-service.git
cd predictive-propositions-service
```

---

## Step 2: Copy Environment Configuration

```bash
cp .env.example .env
```

---

## Step 3: Start All Services (Docker Compose)

```bash
docker-compose -f docker/docker-compose.yml up -d
```

This will start:
- ✅ **Predictive Propositions API** on http://localhost:8000
- ✅ **PostgreSQL Database** on localhost:5432
- ✅ **Redis Cache** on localhost:6379
- ✅ **Kafka Broker** on localhost:9092
- ✅ **Zookeeper** on localhost:2181

---

## Step 4: Wait for Services to Be Healthy

```bash
# Check container status
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f api
```

Wait until you see: **"Predictive Propositions Service v0.1.0"**

---

## Step 5: Access the API

### Health Check
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "predictive-propositions-service",
  "version": "0.1.0",
  "timestamp": "2025-12-13T23:00:00Z"
}
```

### API Documentation (Swagger UI)

Open in browser: **http://localhost:8000/docs**

### ReDoc Documentation

Open in browser: **http://localhost:8000/redoc**

---

## Step 6: Test the API

### Get Suggestions

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
      "id": "prop_0",
      "title": "Suggestion 1",
      "confidence": 0.8,
      "reason": "rule-based ranking (frequency + popularity)"
    },
    ...
  ],
  "served_by": "rule_based_ranker",
  "latency_ms": 12.34,
  "timestamp": "2025-12-13T23:00:00Z"
}
```

### Log an Event

```bash
curl -X POST http://localhost:8000/log_event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "click",
    "user_id": "user_123",
    "proposition_id": "prop_0",
    "timestamp": "2025-12-13T23:00:00Z"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Event logged: click",
  "event_count": 1
}
```

### Get Events

```bash
curl http://localhost:8000/events?limit=10
```

### Get Metrics

```bash
curl http://localhost:8000/metrics
```

---

## Step 7: Run ML Training (Optional)

```bash
python ml_training/train.py
```

This will:
- Generate synthetic training data (5000 samples)
- Train logistic regression model
- Save model to `src/ml/models/ranker_v1.pkl`
- Save scaler to `src/ml/models/scaler_v1.pkl`

---

## Step 8: Run Tests (Optional)

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## Management Commands

### View Logs

```bash
# All services
docker-compose -f docker/docker-compose.yml logs -f

# Only API
docker-compose -f docker/docker-compose.yml logs -f api

# PostgreSQL
docker-compose -f docker/docker-compose.yml logs -f db
```

### Stop Services

```bash
docker-compose -f docker/docker-compose.yml down
```

### Stop and Remove Volumes

```bash
docker-compose -f docker/docker-compose.yml down -v
```

### Restart Services

```bash
docker-compose -f docker/docker-compose.yml restart
```

---

## Port Forwarding (If Using Remote Docker)

```bash
# Forward API
ssh -L 8000:localhost:8000 user@remote-host

# Forward PostgreSQL
ssh -L 5432:localhost:5432 user@remote-host
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Out of Memory

```bash
# Increase Docker resources in settings, then:
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d
```

### Database Connection Failed

```bash
# Check PostgreSQL health
docker-compose -f docker/docker-compose.yml exec db pg_isready -U propositions
```

### Redis Connection Failed

```bash
# Check Redis
docker-compose -f docker/docker-compose.yml exec redis redis-cli ping
```

---

## Next Steps

1. **Read the full documentation:** Check README.md
2. **Review deployment options:** See DEPLOYMENT.md
3. **Check phases roadmap:** See PHASES_COMPLETION.md
4. **Explore GitHub Issues:** https://github.com/romanchaa997/predictive-propositions-service/issues
5. **Deploy to production:** Use k8s/deployment.yaml for Kubernetes

---

## Support

For issues, open a GitHub issue: https://github.com/romanchaa997/predictive-propositions-service/issues

---

**Status:** 🚀 Ready to go!
