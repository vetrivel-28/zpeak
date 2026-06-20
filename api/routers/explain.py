from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from api import schemas
from api import services

router = APIRouter()

@router.get("/health", response_model=schemas.HealthResponse)
def health_check():
    return {"status": "ok", "service": "Meeting Knowledge Assistant"}

@router.post("/explain", response_model=schemas.ExplainResponse)
def explain_text(request: schemas.ExplainRequest):
    try:
        results = services.explain_text(request.text)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

def validate_term_input(term: str) -> bool:
    if len(term) > 50:
        return False
    if len(term.split()) > 4:
        return False
    if any(char in term for char in ['.', ',', '?', '!']):
        return False
    return True

@router.post("/term", response_model=schemas.TermResponse)
def explain_term(request: schemas.TermRequest):
    if not validate_term_input(request.term):
        return JSONResponse(status_code=400, content={"error": "Use /explain for sentences and transcripts"})
        
    try:
        result = services.explain_single_term(request.term)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/search")
def search(q: str):
    try:
        results = services.search_terms(q)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats", response_model=schemas.StatsResponse)
def get_stats():
    try:
        stats = services.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
