from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ExplainRequest(BaseModel):
    text: str

class TermRequest(BaseModel):
    term: str

class TermDetail(BaseModel):
    term: str
    definition: str
    category: str
    term_type: str
    source: str
    confidence: str
    matched_text: Optional[str] = None
    difficulty: Optional[str] = None
    saved: Optional[bool] = None

class ExplainResponse(BaseModel):
    known_terms: List[Dict[str, Any]]
    new_terms: List[Dict[str, Any]]
    unknown_terms: List[str]

class TermResponse(BaseModel):
    term: str
    definition: str
    category: str
    source: str
    saved: Optional[bool] = None

class HealthResponse(BaseModel):
    status: str
    service: str

class StatsResponse(BaseModel):
    total_terms: int
    categories: Dict[str, int]
    ai_generated: int
