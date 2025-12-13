# Production Deployment Guide

## Quick Start - Docker Compose (Local/Development)

For local development and testing, use Docker Compose:

```bash
# Clone the repository
git clone https://github.com/romanchaa997/predictive-propositions-service.git
cd predictive-propositions-service

# Copy environment configuration
cp .env.example .env

# Start all services (API, PostgreSQL, Redis, Kafka, Zookeeper)
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be healthy (~30 seconds)
docker-compose -f docker/docker-compose.yml logs -f api

# Access the service
API: http://localhost:8000
API Docs (Swagger): http://localhost:8000/docs
PostgreSQL: localhost:5432
Redis: localhost:6379
Kafka: localhost:9092
```

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Get suggestions
curl -X POST http://localhost:8000/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "context": "search_query",
    "context_type": "search",
    "limit": 5,
    "device": "mobile"
  }'

# Log an event
curl -X POST http://localhost:8000/log_event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "click",
    "user_id": "user_123",
    "proposition_id": "prop_1",
    "timestamp": "2025-12-13T23:00:00Z"
  }'
```

### Stop Services

```bash
# Stop all containers
docker-compose -f docker/docker-compose.yml down

# Remove volumes (warning: this deletes data)
docker-compose -f docker/docker-compose.yml down -v
```

---

## Production Deployment - Kubernetes

For production environments, deploy on Kubernetes:

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- kubectl configured
- Docker image pushed to registry (e.g., Docker Hub, ECR, GCR)

### Build & Push Docker Image

```bash
# Build image
docker build -t romanchaa997/propositions-api:0.1.0 -f docker/Dockerfile .

# Push to registry
docker push romanchaa997/propositions-api:0.1.0
```

### Create Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace propositions

# Create secrets for database and redis URLs
kubectl create secret generic propositions-secrets \
  --from-literal=database-url="postgresql://user:password@db-service:5432/propositions" \
  --from-literal=redis-url="redis://redis-service:6379/0" \
  -n propositions
```

### Deploy Services

```bash
# Deploy API service
kubectl apply -f k8s/deployment.yaml -n propositions

# Check deployment status
kubectl get pods -n propositions
kubectl get svc -n propositions
kubectl describe pod <pod-name> -n propositions

# View logs
kubectl logs -f deployment/propositions-api -n propositions
```

### Verify Deployment

```bash
# Port forward to test locally
kubectl port-forward svc/propositions-api 8000:80 -n propositions

# Test API
curl http://localhost:8000/health

# Get external IP (for LoadBalancer)
kubectl get svc propositions-api -n propositions -o wide
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment propositions-api --replicas=5 -n propositions

# HorizontalPodAutoscaler is configured in deployment.yaml
# It will automatically scale between 3-10 replicas based on CPU/memory
```

### Monitoring

```bash
# Watch deployment status
kubectl rollout status deployment/propositions-api -n propositions

# View metrics (requires metrics server)
kubectl top nodes
kubectl top pods -n propositions
```

### Updates (Zero-Downtime)

```bash
# Push new image
docker build -t romanchaa997/propositions-api:0.2.0 -f docker/Dockerfile .
docker push romanchaa997/propositions-api:0.2.0

# Update deployment (rolling update configured)
kubectl set image deployment/propositions-api \
  api=romanchaa997/propositions-api:0.2.0 \
  -n propositions

# Monitor rollout
kubectl rollout status deployment/propositions-api -n propositions

# Rollback if needed
kubectl rollout undo deployment/propositions-api -n propositions
```

---

## Environment Variables

See `.env.example` for all configuration options:

- `APP_ENV`: "development" or "production"
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `KAFKA_BROKER`: Kafka broker address
- `ENABLE_ML_RANKING`: Enable ML model (false for Phase 1)
- `CACHE_TTL`: Cache time-to-live (seconds)

---

## Health & Readiness Probes

- **Liveness Probe**: `GET /health` every 10s (starts after 30s)
- **Readiness Probe**: `GET /health` every 5s (starts after 10s)
- Containers restart if liveness fails 3 times
- Remove from load balancer if readiness fails 2 times

---

## Monitoring & Logging

- **Metrics Endpoint**: `GET /metrics` (Prometheus format)
- **Structured Logging**: JSON logs sent to stdout
- **Log Level**: Configurable via `LOG_LEVEL` env var
- Integrate with: ELK, Datadog, Splunk, Grafana Loki

---

## Support

For issues or questions, open a GitHub issue or contact the maintainers.

Status: 🚀 Ready for production deployment (Phase 1)
