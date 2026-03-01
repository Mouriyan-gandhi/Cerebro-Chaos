"""
Cerebro Chaos - Pydantic Schemas (Request/Response models)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Repository Schemas ────────────────────────────────────────

class RepoImportRequest(BaseModel):
    url: str = Field(..., description="GitHub repository URL")
    branch: str = Field(default="main", description="Branch to analyze")


class ServiceOut(BaseModel):
    id: str
    name: str
    service_type: Optional[str] = None
    file_path: Optional[str] = None
    description: Optional[str] = None
    dependencies: List[str] = []
    endpoints: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True


class RiskOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    category: Optional[str] = None
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    failure_probability: float = 0.0
    impact_score: float = 0.0
    fix_suggestion: Optional[str] = None
    fix_code: Optional[str] = None
    is_resolved: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChaosTestRequest(BaseModel):
    risk_id: Optional[str] = None
    test_type: str = "latency"
    target_service: Optional[str] = None
    config: Dict[str, Any] = {}


class ChaosTestOut(BaseModel):
    id: str
    test_type: str
    target_service: Optional[str] = None
    status: str = "pending"
    baseline_latency: Optional[float] = None
    chaos_latency: Optional[float] = None
    error_rate_before: Optional[float] = None
    error_rate_after: Optional[float] = None
    cascading_failures: List[str] = []
    result_summary: Optional[str] = None
    failure_probability: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RepoOut(BaseModel):
    id: str
    url: str
    name: str
    owner: Optional[str] = None
    branch: str = "main"
    status: str = "pending"
    language: Optional[str] = None
    file_count: int = 0
    total_lines: int = 0
    created_at: Optional[datetime] = None
    services: List[ServiceOut] = []
    risks: List[RiskOut] = []
    chaos_tests: List[ChaosTestOut] = []
    
    class Config:
        from_attributes = True


class DependencyGraph(BaseModel):
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []


class AnalysisResult(BaseModel):
    repository: RepoOut
    dependency_graph: DependencyGraph
    risks: List[RiskOut] = []
    summary: Dict[str, Any] = {}


class FixSuggestion(BaseModel):
    risk_id: str
    title: str
    description: str
    original_code: Optional[str] = None
    suggested_code: Optional[str] = None
    confidence: float = 0.0
    implementation_effort: str = "medium"  # low, medium, high
