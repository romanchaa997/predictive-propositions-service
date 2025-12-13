# Predictive Propositions Service - Startup Guide

## Quick Start (5 Minutes)

Get the service running locally with Docker Compose:

### 1. Prerequisites
Ensure you have:
- ✅ Docker & Docker Compose installed
- ✅ Git installed
- ✅ ~2GB free disk space
- ✅ Ports available: 8000 (API), 5432 (DB), 6379 (Redis), 9092 (Kafka), 2181 (Zookeeper)

### 2. Clone Repository
```bash
git clone https://github.com/romanchaa997/predictive-propositions-service.git
cd predictive-propositions-service
```

### 3. Setup Environment
```bash
cp .env.example .env
```

### 4. Start All Services
```bash
docker-compose -f docker/docker-compose.yml up -d
```

This starts:
- **API Server:** http://localhost:8000 ✅
- **PostgreSQL:** localhost:5432
- **Redis Cache:** localhost:6379
- **Kafka Broker:** localhost:9092
- **Zookeeper:** localhost:2181

### 5. Verify Services

#### Check Container Status
```bash
docker-compose -f docker/docker-compose.yml ps
```

You should see all 5 containers **Up**:
```
NAME                  STATUS
props-api            Up 30s
props-db             Up 40s
props-redis          Up 35s
props-kafka          Up 30s
props-zookeeper      Up 45s
```

#### Check API Logs
```bash
docker-compose -f docker/docker-compose.yml logs -f api
```

Wait for:
```
Predictive Propositions Service v0.1.0
Application startup complete
```

#### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-12T00:00:00Z"
}
```

### 6. Access the API

**Interactive API Documentation:** http://localhost:8000/docs

**Get Suggestions:**
```bash
curl -X POST http://localhost:8000/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "context": {"page": "home"},
    "limit": 5
  }'
```

**Expected Response:**
```json
{
  "user_id": "user_123",
  "propositions": [
    {
      "id": "prop_1",
      "title": "Recommended Action 1",
      "score": 0.95
    }
  ]
}
```

**Log an Event:**
```bash
curl -X POST http://localhost:8000/log_event \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "event_type": "click",
    "proposition_id": "prop_1",
    "context": {"page": "home"},
    "timestamp": "2025-01-12T00:00:00Z"
  }'
```

---

## Detailed Service Info

### Docker Compose Services

| Service | Port | Purpose | Health Check |
|---------|------|---------|---------------|
| **API** | 8000 | FastAPI application | `GET /health` |
| **PostgreSQL** | 5432 | Feature store & events | `psql -c SELECT 1` |
| **Redis** | 6379 | Response caching | `redis-cli ping` |
| **Kafka** | 9092 | Event streaming | Port open |
| **Zookeeper** | 2181 | Kafka coordination | Port open |

### Service Dependencies

```
API (FastAPI)
├── PostgreSQL (data persistence)
├── Redis (caching)
└── Kafka (event queue)
    └── Zookeeper (coordination)
```

---

## Troubleshooting

### Port Already in Use

If port 8000 is busy:
```bash
# Change API port in docker-compose.yml:
# ports:
#   - "8001:8000"  # Use 8001 instead

docker-compose -f docker/docker-compose.yml up -d
curl http://localhost:8001/health
```

### Services Won't Start

```bash
# Check logs
docker-compose -f docker/docker-compose.yml logs

# Restart services
docker-compose -f docker/docker-compose.yml restart

# Full clean restart
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d
```

### Containers Exit with Error

```bash
# View specific service logs
docker-compose -f docker/docker-compose.yml logs api
docker-compose -f docker/docker-compose.yml logs db

# Check resource usage
docker stats
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
docker-compose -f docker/docker-compose.yml exec db psql -U postgres -d propositions -c "SELECT 1"

# Check Redis connection
docker-compose -f docker/docker-compose.yml exec redis redis-cli ping
```

---

## Common Tasks

### View Live Logs
```bash
# Follow API logs
docker-compose -f docker/docker-compose.yml logs -f api

# Last 100 lines of all services
docker-compose -f docker/docker-compose.yml logs --tail=100
```

### Stop Services
```bash
# Pause (can be restarted)
docker-compose -f docker/docker-compose.yml stop

# Resume
docker-compose -f docker/docker-compose.yml start

# Stop and remove containers
docker-compose -f docker/docker-compose.yml down
```

### Clean Up (Reset Everything)
```bash
# Remove containers, volumes, networks
docker-compose -f docker/docker-compose.yml down -v

# Remove all images
docker-compose -f docker/docker-compose.yml down -v --rmi all
```

### Access Database Directly
```bash
# Connect to PostgreSQL
docker-compose -f docker/docker-compose.yml exec db psql -U postgres -d propositions

# List tables
\dt

# Query events
SELECT * FROM events LIMIT 10;

# Exit
\q
```

### Monitor Container Performance
```bash
# Real-time stats
docker stats

# CPU/Memory usage
docker-compose -f docker/docker-compose.yml stats
```

---

## Testing the API

### Test Health Endpoint
```bash
curl -s http://localhost:8000/health | jq
```

### Test Suggestions Endpoint
```bash
curl -s -X POST http://localhost:8000/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "context": {"page": "home", "device": "mobile"},
    "limit": 3
  }' | jq
```

### Load Test (Basic)
```bash
for i in {1..10}; do
  curl -s http://localhost:8000/health > /dev/null
  echo "Request $i: OK"
done
```

### Using Swagger UI
1. Open: http://localhost:8000/docs
2. Click on any endpoint (e.g., "POST /suggest")
3. Click "Try it out"
4. Fill in sample data
5. Click "Execute"

---

## Development Workflow

### Make Code Changes
```bash
# Edit source code in src/ directory
# Changes are reflected in running container (if volume-mounted)

# Rebuild image if needed
docker-compose -f docker/docker-compose.yml build api
docker-compose -f docker/docker-compose.yml up -d
```

### Run Tests
```bash
# Inside API container
docker-compose -f docker/docker-compose.yml exec api \
  pytest src/tests/ -v
```

### View Container File System
```bash
# SSH into container
docker-compose -f docker/docker-compose.yml exec api bash

# List files
ls -la /app/
ls -la /app/src/
```

---

## Next Steps

1. ✅ **Verify the service is running** → Check http://localhost:8000/docs
2. 📊 **Generate sample data** → Use `/log_event` endpoint
3. 🔄 **Test suggestions** → Use `/suggest` endpoint
4. 📈 **Monitor performance** → Check logs and metrics
5. 📖 **Read full docs** → See `DEPLOYMENT.md` for production setup

---

## Quick Reference

```bash
# Start services
docker-compose -f docker/docker-compose.yml up -d

# Check status
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Test API
curl http://localhost:8000/health

# Stop services
docker-compose -f docker/docker-compose.yml down

# API Documentation
http://localhost:8000/docs
```

---

## Support

- **Issues:** GitHub Issues (https://github.com/romanchaa997/predictive-propositions-service/issues)
- **Documentation:** README.md, DEPLOYMENT.md, QUICK_START.md
- **Status:** Active Development
- **Owner:** @romanchaa997

---

**Version:** 0.1.0  
**Last Updated:** 2025-01-12  
**Status:** ✅ Ready to Run
