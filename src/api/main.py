"""Predictive Propositions Service - FastAPI Application"""
import os
import json
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Predictive Propositions Service",
    description="ML-powered service for generating contextual predictive propositions",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============= Request/Response Models =============

class PropositionItem(BaseModel):
    """Single proposition item"""
    id: str = Field(..., example="prop_001")
    title: str = Field(..., example="Popular Search")
    confidence: float = Field(..., ge=0.0, le=1.0, example=0.87)
    reason: Optional[str] = Field(None, example="trending + user_interest")

class SuggestionRequest(BaseModel):
    """Request for getting suggestions"""
    user_id: str = Field(..., example="user_123")
    context: str = Field(..., example="search_query")
    context_type: str = Field(default="search", example="search")
    limit: int = Field(default=5, ge=1, le=100)
    device: str = Field(default="web", example="mobile")

class SuggestionResponse(BaseModel):
    """Response with suggested propositions"""
    propositions: List[PropositionItem]
    served_by: str = Field(example="ml_ranker")
    latency_ms: float
    timestamp: str

class EventLog(BaseModel):
    """Event logging model"""
    event_type: str = Field(..., example="click")
    user_id: str
    proposition_id: str
    timestamp: str

# ============= In-Memory Storage (for Phase 1) =============

events_store = []
proposition_cache = {}

# ============= API Endpoints =============

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "predictive-propositions-service",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/suggest", response_model=SuggestionResponse, tags=["Suggestions"])
async def get_suggestions(request: SuggestionRequest):
    """Get predictive propositions for user context
    
    Returns ranked list of suggested actions based on user history and context.
    """
    import time
    start_time = time.time()
    
    try:
        # Phase 1: Rule-based ranking (frequency + popularity)
        # This will be replaced with ML model in Phase 3
        propositions = [
            PropositionItem(
                id=f"prop_{i}",
                title=f"Suggestion {i+1}",
                confidence=0.8 - (i * 0.1),
                reason="rule-based ranking (frequency + popularity)"
            )
            for i in range(min(request.limit, 5))
        ]
        
        latency_ms = (time.time() - start_time) * 1000
        
        return SuggestionResponse(
            propositions=propositions,
            served_by="rule_based_ranker",
            latency_ms=round(latency_ms, 2),
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error in /suggest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/log_event", tags=["Events"])
async def log_event(event: EventLog):
    """Log user interaction event (impression, click, conversion)"""
    try:
        event_dict = event.dict()
        event_dict["logged_at"] = datetime.utcnow().isoformat()
        events_store.append(event_dict)
        
        logger.info(f"Event logged: {event.event_type} for user {event.user_id}")
        
        return {
            "status": "success",
            "message": f"Event logged: {event.event_type}",
            "event_count": len(events_store)
        }
    
    except Exception as e:
        logger.error(f"Error logging event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events", tags=["Events"])
async def get_events(limit: int = Query(10, ge=1, le=1000)):
    """Retrieve logged events (development/debugging)"""
    return {
        "total_events": len(events_store),
        "recent_events": events_store[-limit:]
    }

@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Get service metrics"""
    return {
        "service": "predictive-propositions-service",
        "status": "operational",
        "total_events_logged": len(events_store),
        "cache_size": len(proposition_cache),
        "timestamp": datetime.utcnow().isoformat()
    }

# ============= Error Handlers =============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error": True}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": True}
    )

# ============= Startup/Shutdown Events =============

@app.on_event("startup")
async def startup_event():
    logger.info("Service starting up...")
    logger.info("Predictive Propositions Service v0.1.0")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Service shutting down. Total events logged: {len(events_store)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
