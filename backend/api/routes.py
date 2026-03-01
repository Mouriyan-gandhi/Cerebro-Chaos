"""
Cerebro Chaos - API Routes
All REST API endpoints for the application.
"""
import os
import sys
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, Repository, Service, Risk, ChaosTest
from models.schemas import (
    RepoImportRequest, RepoOut, ServiceOut, RiskOut,
    ChaosTestRequest, ChaosTestOut, DependencyGraph,
    AnalysisResult, FixSuggestion,
)
from github_import.service import GitHubImportService
from code_analysis.service import CodeAnalysisEngine
from risk_agent.service import RiskDetectionAgent
from chaos_engine.service import ChaosSimulationEngine
from fix_agent.service import FixRecommendationAgent


router = APIRouter()

# Service instances
github_service = GitHubImportService()
analysis_engine = CodeAnalysisEngine()
risk_agent = RiskDetectionAgent()
chaos_engine = ChaosSimulationEngine()
fix_agent = FixRecommendationAgent()

# In-memory store for analysis results (per repo)
analysis_cache = {}


def run_full_analysis(repo_id: str, repo_url: str, branch: str, db_session_factory):
    """Background task: full pipeline analysis."""
    db = db_session_factory()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            return
        
        # Step 1: Clone repo
        repo.status = "cloning"
        db.commit()
        
        clone_result = github_service.clone_repo(repo_url, branch)
        repo.local_path = clone_result["local_path"]
        repo.language = clone_result["language"]
        repo.file_count = clone_result["file_count"]
        repo.total_lines = clone_result["total_lines"]
        repo.owner = clone_result["owner"]
        db.commit()
        
        # Step 2: Analyze code
        repo.status = "analyzing"
        db.commit()
        
        analysis = analysis_engine.analyze_repository(clone_result["local_path"])
        analysis_cache[repo_id] = analysis
        
        # Save services
        for svc_data in analysis.get("services", []):
            service = Service(
                repository_id=repo_id,
                name=svc_data["name"],
                service_type=svc_data.get("service_type"),
                file_path=svc_data.get("path"),
                description=f"{svc_data.get('service_type', 'Unknown')} service",
                dependencies=[d.get("to") for d in svc_data.get("dependencies", [])],
                endpoints=svc_data.get("endpoints", []),
            )
            db.add(service)
        db.commit()
        
        # Step 3: Detect risks
        repo.status = "risk_detection"
        db.commit()
        
        risks = risk_agent.detect_risks(analysis, clone_result["local_path"])
        
        for risk_data in risks:
            risk = Risk(
                id=risk_data["id"],
                repository_id=repo_id,
                title=risk_data["title"],
                description=risk_data["description"],
                severity=risk_data["severity"],
                category=risk_data["category"],
                file_path=risk_data.get("file_path"),
                line_start=risk_data.get("line_start"),
                line_end=risk_data.get("line_end"),
                code_snippet=risk_data.get("code_snippet"),
                failure_probability=risk_data.get("failure_probability", 0.0),
                impact_score=risk_data.get("impact_score", 0.0),
                fix_suggestion=risk_data.get("fix_suggestion"),
                fix_code=risk_data.get("fix_code"),
            )
            db.add(risk)
        db.commit()
        
        # Step 4: Generate fixes
        fixes = fix_agent.generate_fixes_batch(risks)
        for fix in fixes:
            risk = db.query(Risk).filter(Risk.id == fix["risk_id"]).first()
            if risk:
                risk.fix_suggestion = fix.get("description", "")
                risk.fix_code = fix.get("suggested_code", "")
        db.commit()
        
        # Done
        repo.status = "completed"
        repo.updated_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if repo:
            repo.status = "failed"
            db.commit()
        print(f"Analysis failed for {repo_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ─── Repository Endpoints ────────────────────────────────────

@router.post("/repos/analyze", response_model=RepoOut)
async def analyze_repo(
    request: RepoImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Import and analyze a GitHub repository."""
    # Parse URL to get repo info
    try:
        owner, name = github_service.parse_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if already analyzed
    existing = db.query(Repository).filter(Repository.url == request.url).first()
    if existing and existing.status == "completed":
        return existing
    
    # Create new repository record
    import uuid
    repo = Repository(
        id=str(uuid.uuid4()),
        url=request.url,
        name=name,
        owner=owner,
        branch=request.branch,
        status="pending",
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    
    # Start analysis in background
    from models.database import SessionLocal
    background_tasks.add_task(
        run_full_analysis, repo.id, request.url, request.branch, SessionLocal
    )
    
    return repo


@router.get("/repos", response_model=List[RepoOut])
async def list_repos(db: Session = Depends(get_db)):
    """List all analyzed repositories."""
    repos = db.query(Repository).order_by(Repository.created_at.desc()).all()
    return repos


@router.get("/repos/{repo_id}", response_model=RepoOut)
async def get_repo(repo_id: str, db: Session = Depends(get_db)):
    """Get repository details with services and risks."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/repos/{repo_id}")
async def delete_repo(repo_id: str, db: Session = Depends(get_db)):
    """Delete a repository and its analysis data."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Cleanup cloned files
    if repo.local_path:
        github_service.cleanup(repo.local_path)
    
    db.delete(repo)
    db.commit()
    return {"status": "deleted"}


# ─── Dependency Graph ─────────────────────────────────────────

@router.get("/repos/{repo_id}/graph", response_model=DependencyGraph)
async def get_dependency_graph(repo_id: str, db: Session = Depends(get_db)):
    """Get the dependency graph for a repository."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Check cache
    if repo_id in analysis_cache:
        graph = analysis_cache[repo_id].get("dependency_graph", {})
        return DependencyGraph(**graph)
    
    # Rebuild from DB
    services = db.query(Service).filter(Service.repository_id == repo_id).all()
    nodes = []
    edges = []
    
    for service in services:
        nodes.append({
            "id": service.name,
            "label": service.name,
            "type": service.service_type or "unknown",
        })
        for dep in (service.dependencies or []):
            edges.append({
                "source": service.name,
                "target": dep,
                "type": "depends",
            })
    
    return DependencyGraph(nodes=nodes, edges=edges)


# ─── Risks ────────────────────────────────────────────────────

@router.get("/repos/{repo_id}/risks", response_model=List[RiskOut])
async def get_risks(repo_id: str, db: Session = Depends(get_db)):
    """Get all detected risks for a repository."""
    risks = db.query(Risk).filter(
        Risk.repository_id == repo_id
    ).order_by(Risk.failure_probability.desc()).all()
    return risks


@router.get("/risks/{risk_id}/fix", response_model=FixSuggestion)
async def get_fix(risk_id: str, db: Session = Depends(get_db)):
    """Get fix suggestion for a specific risk."""
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    risk_dict = {
        "id": risk.id,
        "title": risk.title,
        "description": risk.description,
        "severity": risk.severity,
        "category": risk.category,
        "file_path": risk.file_path,
        "code_snippet": risk.code_snippet,
        "fix_suggestion": risk.fix_suggestion,
        "fix_code": risk.fix_code,
    }
    
    fix = fix_agent.generate_fix(risk_dict)
    return FixSuggestion(**fix)


# ─── Chaos Tests ──────────────────────────────────────────────

@router.post("/repos/{repo_id}/chaos", response_model=ChaosTestOut)
async def run_chaos_test(
    repo_id: str,
    request: ChaosTestRequest,
    db: Session = Depends(get_db),
):
    """Run a chaos simulation test."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Get risk if specified
    risk_dict = {}
    if request.risk_id:
        risk = db.query(Risk).filter(Risk.id == request.risk_id).first()
        if risk:
            risk_dict = {
                "id": risk.id,
                "title": risk.title,
                "description": risk.description,
                "severity": risk.severity,
                "category": risk.category,
                "file_path": risk.file_path,
                "failure_probability": risk.failure_probability,
            }
    
    if not risk_dict:
        risk_dict = {
            "id": "generic",
            "title": "Generic Test",
            "file_path": request.target_service or "",
            "failure_probability": 0.5,
        }
    
    # Get analysis data
    analysis = analysis_cache.get(repo_id, {})
    services = analysis.get("services", [])
    graph = analysis.get("dependency_graph", {"nodes": [], "edges": []})
    indicators = analysis.get("reliability_indicators", {})
    
    # Create and run simulation
    simulation = chaos_engine.create_simulation(
        test_type=request.test_type,
        risk=risk_dict,
        services=services,
        dependency_graph=graph,
        config=request.config,
    )
    
    result = chaos_engine.run_simulation(
        simulation["id"], services, graph, indicators
    )
    
    # Save to DB
    chaos_test = ChaosTest(
        id=result["id"],
        repository_id=repo_id,
        risk_id=request.risk_id,
        test_type=request.test_type,
        target_service=result.get("target_service"),
        status=result["status"],
        config=result.get("config", {}),
        baseline_latency=result.get("baseline_latency"),
        chaos_latency=result.get("chaos_latency"),
        error_rate_before=result.get("error_rate_before"),
        error_rate_after=result.get("error_rate_after"),
        cascading_failures=result.get("cascading_failures", []),
        result_summary=result.get("result_summary"),
        failure_probability=result.get("failure_probability"),
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    db.add(chaos_test)
    db.commit()
    
    return chaos_test


@router.get("/repos/{repo_id}/chaos", response_model=List[ChaosTestOut])
async def list_chaos_tests(repo_id: str, db: Session = Depends(get_db)):
    """List all chaos tests for a repository."""
    tests = db.query(ChaosTest).filter(
        ChaosTest.repository_id == repo_id
    ).order_by(ChaosTest.created_at.desc()).all()
    return tests


# ─── Dashboard Stats ──────────────────────────────────────────

@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get overall dashboard statistics."""
    total_repos = db.query(Repository).count()
    total_risks = db.query(Risk).count()
    total_tests = db.query(ChaosTest).count()
    
    critical_risks = db.query(Risk).filter(Risk.severity == "critical").count()
    high_risks = db.query(Risk).filter(Risk.severity == "high").count()
    medium_risks = db.query(Risk).filter(Risk.severity == "medium").count()
    
    resolved_risks = db.query(Risk).filter(Risk.is_resolved == True).count()
    
    # Average failure probability
    from sqlalchemy import func
    avg_failure = db.query(func.avg(Risk.failure_probability)).scalar() or 0
    
    return {
        "total_repos": total_repos,
        "total_risks": total_risks,
        "total_tests": total_tests,
        "critical_risks": critical_risks,
        "high_risks": high_risks,
        "medium_risks": medium_risks,
        "resolved_risks": resolved_risks,
        "avg_failure_probability": round(float(avg_failure), 2),
        "risk_breakdown": {
            "critical": critical_risks,
            "high": high_risks,
            "medium": medium_risks,
            "low": db.query(Risk).filter(Risk.severity == "low").count(),
        },
    }
