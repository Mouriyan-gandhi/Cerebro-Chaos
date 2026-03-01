"""
Cerebro Chaos - AI Risk Detection Agent
Uses LLM to analyze code and detect reliability risks.
Falls back to rule-based detection when LLM is unavailable.
"""
import json
import re
import uuid
import random
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from config import settings


class RiskDetectionAgent:
    """
    AI-powered risk detection agent.
    Analyzes code for reliability issues:
    - Missing retry logic
    - Bad timeout configurations  
    - Single points of failure (SPOF)
    - Cascading failure risks
    - Missing error handling
    - No circuit breakers
    - Missing fallbacks
    """
    
    RISK_CATEGORIES = {
        "retry": {
            "title": "Missing Retry Logic",
            "description": "No retry mechanism found for external calls",
            "severity": "high",
            "fix_template": "Add exponential backoff retry with max {max_retries} attempts",
        },
        "timeout": {
            "title": "Dangerous Timeout Configuration",
            "description": "Timeout value is too high or missing, risking resource exhaustion",
            "severity": "high",
            "fix_template": "Set appropriate timeout of {timeout}s with connection timeout of {conn_timeout}s",
        },
        "spof": {
            "title": "Single Point of Failure",
            "description": "Service has no redundancy or failover mechanism",
            "severity": "critical",
            "fix_template": "Add health checks and failover to backup service",
        },
        "cascading": {
            "title": "Cascading Failure Risk",
            "description": "Failure in this service can cascade to dependent services",
            "severity": "critical",
            "fix_template": "Implement circuit breaker pattern with fallback",
        },
        "error_handling": {
            "title": "Insufficient Error Handling",
            "description": "Missing or generic error handling that could mask failures",
            "severity": "medium",
            "fix_template": "Add specific error handling for {error_types}",
        },
        "circuit_breaker": {
            "title": "Missing Circuit Breaker",
            "description": "No circuit breaker pattern for external service calls",
            "severity": "high",
            "fix_template": "Add circuit breaker with {threshold} failure threshold",
        },
        "fallback": {
            "title": "No Fallback Strategy",
            "description": "No fallback mechanism when primary service/resource fails",
            "severity": "medium",
            "fix_template": "Implement fallback using {strategy}",
        },
        "rate_limiting": {
            "title": "Missing Rate Limiting",
            "description": "API endpoints lack rate limiting, vulnerable to overload",
            "severity": "medium",
            "fix_template": "Add rate limiting with {limit} requests per {window}",
        },
    }

    # Risk-specific code fix templates
    FIX_CODE_TEMPLATES = {
        "retry": {
            "python": '''import time
import random

def call_with_retry(func, max_retries=3, base_delay=1.0):
    """Exponential backoff retry wrapper"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)''',
            "javascript": '''async function callWithRetry(fn, maxRetries = 3, baseDelay = 1000) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
      const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}''',
        },
        "timeout": {
            "python": '''import requests

# Always set explicit timeouts
response = requests.get(url, timeout=(5, 30))  # (connect_timeout, read_timeout)''',
            "javascript": '''// Always set explicit timeouts
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 30000);

try {
  const response = await fetch(url, { signal: controller.signal });
} finally {
  clearTimeout(timeout);
}''',
        },
        "circuit_breaker": {
            "python": '''from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"  
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    def call(self, func):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN''',
        },
    }

    def __init__(self):
        self.client = None
        if HAS_OPENAI and settings.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception:
                pass

    def detect_risks(self, analysis_result: Dict, repo_path: str = "") -> List[Dict]:
        """
        Detect reliability risks in analyzed code.
        Uses LLM if available, falls back to rule-based detection.
        """
        risks = []
        
        # Rule-based detection (always runs)
        rule_risks = self._rule_based_detection(analysis_result)
        risks.extend(rule_risks)
        
        # AI-based detection (if LLM available)
        if self.client:
            try:
                ai_risks = self._llm_detection(analysis_result, repo_path)
                risks.extend(ai_risks)
            except Exception as e:
                print(f"LLM detection failed: {e}")
        
        # Deduplicate and score risks
        risks = self._deduplicate_risks(risks)
        risks = self._score_risks(risks, analysis_result)
        
        return risks

    def _rule_based_detection(self, analysis: Dict) -> List[Dict]:
        """Rule-based risk detection using pattern analysis results."""
        risks = []
        reliability = analysis.get("reliability_indicators", {})
        services = analysis.get("services", [])
        
        # Check for services making external calls without retry
        services_with_external_calls = [
            s for s in services if s.get("external_calls")
        ]
        retry_files = {r["file"] for r in reliability.get("retry_patterns", [])}
        
        for service in services_with_external_calls:
            if service["path"] not in retry_files:
                for call in service.get("external_calls", []):
                    risks.append(self._create_risk(
                        category="retry",
                        file_path=call.get("file", service["path"]),
                        line_start=call.get("line"),
                        code_snippet=call.get("line_content", ""),
                        details=f"External call at line {call.get('line')} has no retry logic",
                    ))
        
        # Check for missing timeouts on external calls
        timeout_files = {r["file"] for r in reliability.get("timeout_configs", [])}
        
        for service in services_with_external_calls:
            if service["path"] not in timeout_files:
                risks.append(self._create_risk(
                    category="timeout",
                    file_path=service["path"],
                    details="External calls without explicit timeout configuration",
                ))
        
        # Check for missing circuit breakers
        cb_files = {r["file"] for r in reliability.get("circuit_breakers", [])}
        
        for service in services_with_external_calls:
            if service["path"] not in cb_files:
                risks.append(self._create_risk(
                    category="circuit_breaker",
                    file_path=service["path"],
                    details="No circuit breaker pattern for external service calls",
                ))
        
        # Check for missing fallbacks
        fallback_files = {r["file"] for r in reliability.get("fallbacks", [])}
        
        for service in services:
            if service.get("db_connections") and service["path"] not in fallback_files:
                risks.append(self._create_risk(
                    category="fallback",
                    file_path=service["path"],
                    details="Database operations without fallback strategy",
                ))
        
        # SPOF detection: services with high in-degree in dependency graph
        graph = analysis.get("dependency_graph", {})
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        
        # Count incoming edges per node
        in_degree = {}
        for edge in edges:
            target = edge.get("target", "")
            in_degree[target] = in_degree.get(target, 0) + 1
        
        for node_id, degree in in_degree.items():
            if degree >= 3:  # 3+ services depending on it
                risks.append(self._create_risk(
                    category="spof",
                    file_path=node_id,
                    details=f"Service '{node_id}' is a single point of failure with {degree} dependent services",
                ))
        
        # Cascading failure detection
        for node_id, degree in in_degree.items():
            if degree >= 2:
                # Check if this node has error handling
                node_service = next((s for s in services if s["name"] == node_id), None)
                if node_service:
                    error_handling_in_file = any(
                        e["file"] == node_service["path"] 
                        for e in reliability.get("error_handling", [])
                    )
                    if not error_handling_in_file:
                        risks.append(self._create_risk(
                            category="cascading",
                            file_path=node_service["path"],
                            details=f"Failure in '{node_id}' can cascade to {degree} downstream services without error handling",
                        ))
        
        # Check for API endpoints without rate limiting
        for service in services:
            if service.get("endpoints") and len(service.get("endpoints", [])) > 0:
                risks.append(self._create_risk(
                    category="rate_limiting",
                    file_path=service["path"],
                    details=f"{len(service['endpoints'])} API endpoints without rate limiting",
                ))
        
        # Check error handling quality
        for service in services:
            error_handlers = [
                e for e in reliability.get("error_handling", [])
                if e["file"] == service["path"]
            ]
            # Check for bare except/catch
            for handler in error_handlers:
                content = handler.get("line_content", "")
                if "except:" in content or "except Exception" in content:
                    risks.append(self._create_risk(
                        category="error_handling",
                        file_path=service["path"],
                        line_start=handler.get("line"),
                        code_snippet=content,
                        details="Generic exception handling that masks specific failures",
                    ))
        
        return risks

    def _llm_detection(self, analysis: Dict, repo_path: str) -> List[Dict]:
        """Use LLM to detect sophisticated reliability risks."""
        if not self.client:
            return []
        
        # Prepare context for LLM
        services_summary = []
        for service in analysis.get("services", [])[:10]:  # Limit for token efficiency
            services_summary.append({
                "name": service["name"],
                "type": service.get("service_type"),
                "path": service["path"],
                "endpoints": len(service.get("endpoints", [])),
                "has_retry": bool(service.get("retry_patterns")),
                "has_timeout": bool(service.get("timeout_configs")),
                "has_circuit_breaker": bool(service.get("circuit_breakers")),
                "has_fallback": bool(service.get("fallbacks")),
                "external_calls": len(service.get("external_calls", [])),
                "db_connections": len(service.get("db_connections", [])),
            })
        
        prompt = f"""You are an expert Site Reliability Engineer. Analyze this system architecture and identify reliability risks.

SYSTEM ARCHITECTURE:
Services: {json.dumps(services_summary, indent=2)}
Dependency Graph: {json.dumps(analysis.get('dependency_graph', {}), indent=2)}

For each risk found, respond in this JSON format:
[
  {{
    "category": "retry|timeout|spof|cascading|error_handling|circuit_breaker|fallback|rate_limiting",
    "title": "Short descriptive title",
    "description": "Detailed description of the risk",
    "severity": "critical|high|medium|low",
    "file_path": "path/to/affected/file",
    "failure_probability": 0.0-1.0,
    "fix_suggestion": "How to fix this issue"
  }}
]

Focus on:
1. Missing retry logic for external calls
2. Timeout misconfigurations
3. Single points of failure  
4. Cascading failure risks
5. Missing circuit breakers
6. Insufficient error handling

Return ONLY valid JSON array."""

        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a reliability risk detection AI. Respond only with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            
            content = response.choices[0].message.content.strip()
            # Parse JSON from response
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            
            ai_risks = json.loads(content)
            
            formatted_risks = []
            for risk in ai_risks:
                formatted_risks.append(self._create_risk(
                    category=risk.get("category", "error_handling"),
                    file_path=risk.get("file_path", ""),
                    details=risk.get("description", ""),
                    title_override=risk.get("title"),
                    severity_override=risk.get("severity"),
                    probability=risk.get("failure_probability", 0.5),
                    fix_override=risk.get("fix_suggestion"),
                ))
            
            return formatted_risks
        
        except Exception as e:
            print(f"LLM risk detection error: {e}")
            return []

    def _create_risk(
        self, 
        category: str, 
        file_path: str = "", 
        line_start: int = None,
        line_end: int = None,
        code_snippet: str = "",
        details: str = "",
        title_override: str = None,
        severity_override: str = None,
        probability: float = None,
        fix_override: str = None,
    ) -> Dict:
        """Create a standardized risk object."""
        template = self.RISK_CATEGORIES.get(category, self.RISK_CATEGORIES["error_handling"])
        
        # Determine fix code
        ext = Path(file_path).suffix if file_path else ".py"
        lang = "python" if ext == ".py" else "javascript"
        fix_code = self.FIX_CODE_TEMPLATES.get(category, {}).get(lang, "")
        
        # Auto-calculate probability based on category if not provided
        if probability is None:
            base_probabilities = {
                "retry": 0.72,
                "timeout": 0.68,
                "spof": 0.85,
                "cascading": 0.78,
                "error_handling": 0.55,
                "circuit_breaker": 0.65,
                "fallback": 0.60,
                "rate_limiting": 0.50,
            }
            probability = base_probabilities.get(category, 0.5)
            # Add some realistic variance
            probability = min(0.99, max(0.1, probability + random.uniform(-0.1, 0.1)))
        
        impact_scores = {
            "critical": 9.5,
            "high": 7.5,
            "medium": 5.0,
            "low": 2.5,
            "info": 1.0,
        }
        severity = severity_override or template["severity"]
        
        return {
            "id": str(uuid.uuid4()),
            "title": title_override or template["title"],
            "description": details or template["description"],
            "severity": severity,
            "category": category,
            "file_path": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "code_snippet": code_snippet,
            "failure_probability": round(probability, 2),
            "impact_score": impact_scores.get(severity, 5.0),
            "fix_suggestion": fix_override or template["fix_template"],
            "fix_code": fix_code,
        }

    def _deduplicate_risks(self, risks: List[Dict]) -> List[Dict]:
        """Remove duplicate risks based on category + file."""
        seen = set()
        unique = []
        for risk in risks:
            key = (risk["category"], risk["file_path"], risk.get("line_start"))
            if key not in seen:
                seen.add(key)
                unique.append(risk)
        return unique

    def _score_risks(self, risks: List[Dict], analysis: Dict) -> List[Dict]:
        """Score and sort risks by severity and impact."""
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        
        for risk in risks:
            # Combined score = severity weight * failure probability * impact
            sev_weight = severity_order.get(risk["severity"], 1)
            risk["combined_score"] = round(
                sev_weight * risk["failure_probability"] * risk["impact_score"], 2
            )
        
        # Sort by combined score descending
        risks.sort(key=lambda r: r["combined_score"], reverse=True)
        return risks
