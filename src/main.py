main.py"""FastAPI application for Predictive Propositions Service."""
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging

from storage.database import get_db, init_db
from storage.repositories import (
    UserRepository,
    PropositionRepository,
    InteractionRepository,
    FeatureRepository
)
from storage.models import (
    User, Proposition, Interaction, Feature,
    PropositionType
)

logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Predictive Propositions Service",
    description="ML-powered service for generating contextual predictive propositions",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "predictive-propositions-service",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============== USER ENDPOINTS ==============

@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Retrieve a user by ID."""
    repo = UserRepository(db)
    user = repo.read(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/api/v1/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List users with pagination."""
    repo = UserRepository(db)
    if active_only:
        users = repo.get_active_users(skip=skip, limit=limit)
    else:
        users = repo.read_all(skip=skip, limit=limit)
    return {"items": users, "total": repo.count()}

@app.post("/api/v1/users")
async def create_user(
    username: str,
    email: str,
    db: Session = Depends(get_db)
):
    """Create a new user."""
    repo = UserRepository(db)
    
    # Check if user already exists
    if repo.get_by_username(username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if repo.get_by_email(email):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user = repo.create({
        "username": username,
        "email": email,
        "is_active": True
    })
    return user

@app.put("/api/v1/users/{user_id}/deactivate")
async def deactivate_user(user_id: UUID, db: Session = Depends(get_db)):
    """Deactivate a user account."""
    repo = UserRepository(db)
    success = repo.deactivate_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deactivated", "user_id": user_id}

@app.put("/api/v1/users/{user_id}/reactivate")
async def reactivate_user(user_id: UUID, db: Session = Depends(get_db)):
    """Reactivate a user account."""
    repo = UserRepository(db)
    success = repo.reactivate_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "reactivated", "user_id": user_id}

@app.get("/api/v1/users/search")
async def search_users(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Search users by username or email."""
    repo = UserRepository(db)
    results = repo.search_users(q, limit=limit)
    return {"query": q, "results": results}

# ============== PROPOSITION ENDPOINTS ==============

@app.get("/api/v1/propositions/{proposition_id}")
async def get_proposition(proposition_id: UUID, db: Session = Depends(get_db)):
    """Retrieve a proposition by ID."""
    repo = PropositionRepository(db)
    prop = repo.read(proposition_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proposition not found")
    return prop

@app.get("/api/v1/users/{user_id}/propositions")
async def get_user_propositions(
    user_id: UUID,
    status_filter: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get propositions for a specific user."""
    repo = PropositionRepository(db)
    props = repo.get_propositions_by_user(user_id, skip=skip, limit=limit)
    if status_filter:
        props = [p for p in props if p.status == status_filter]
    return {"user_id": user_id, "propositions": props}

@app.post("/api/v1/propositions")
async def create_proposition(
    user_id: UUID,
    proposition_type: PropositionType,
    title: str,
    description: str,
    confidence_score: float = Query(..., ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """Create a new proposition for a user."""
    # Verify user exists
    user_repo = UserRepository(db)
    if not user_repo.exists(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = PropositionRepository(db)
    prop = repo.create({
        "user_id": user_id,
        "proposition_type": proposition_type,
        "title": title,
        "description": description,
        "confidence_score": confidence_score,
        "status": "pending"
    })
    return prop

# ============== INTERACTION ENDPOINTS ==============

@app.post("/api/v1/interactions")
async def record_interaction(
    user_id: UUID,
    proposition_id: UUID,
    interaction_type: str,
    duration_seconds: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Record a user interaction with a proposition."""
    repo = InteractionRepository(db)
    interaction = repo.create({
        "user_id": user_id,
        "proposition_id": proposition_id,
        "interaction_type": interaction_type,
        "duration_seconds": duration_seconds
    })
    return interaction

@app.get("/api/v1/propositions/{proposition_id}/interactions")
async def get_proposition_interactions(
    proposition_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all interactions for a proposition."""
    repo = InteractionRepository(db)
    interactions = repo.get_interactions_by_proposition(proposition_id, skip=skip, limit=limit)
    return {"proposition_id": proposition_id, "interactions": interactions}

# ============== FEATURE ENDPOINTS ==============

@app.get("/api/v1/features")
async def list_features(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all ML features."""
    repo = FeatureRepository(db)
    features = repo.read_all(skip=skip, limit=limit)
    return {"features": features, "total": repo.count()}

@app.post("/api/v1/features")
async def create_feature(
    name: str,
    feature_type: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new ML feature."""
    repo = FeatureRepository(db)
    feature = repo.create({
        "name": name,
        "feature_type": feature_type,
        "description": description,
        "is_active": True
    })
    return feature

# ============== ANALYTICS ENDPOINTS ==============

@app.get("/api/v1/analytics/user-count")
async def get_user_count(active_only: bool = Query(False), db: Session = Depends(get_db)):
    """Get total user count."""
    repo = UserRepository(db)
    if active_only:
        count = repo.count_active_users()
        return {"active_users": count}
    else:
        count = repo.count()
        return {"total_users": count}

@app.get("/api/v1/analytics/proposition-stats")
async def get_proposition_stats(db: Session = Depends(get_db)):
    """Get proposition statistics."""
    repo = PropositionRepository(db)
    total = repo.count()
    pending = repo.count({"status": "pending"})
    accepted = repo.count({"status": "accepted"})
    rejected = repo.count({"status": "rejected"})
    
    return {
        "total_propositions": total,
        "pending": pending,
        "accepted": accepted,
        "rejected": rejected
    }

# ============== ERROR HANDLERS ==============

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle value errors."""
    return {"detail": str(exc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
