"""
Cerebro Chaos - Fix Recommendation Agent
Generates fix suggestions for detected reliability risks.
Uses LLM when available, falls back to template-based fixes.
"""
import json
import uuid
from typing import Dict, List, Any, Optional

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from config import settings


class FixRecommendationAgent:
    """
    AI-powered fix recommendation agent.
    Analyzes risks and generates actionable fix suggestions with code examples.
    """
    
    # Comprehensive fix templates per category and language
    FIX_TEMPLATES = {
        "retry": {
            "python": {
                "title": "Add Exponential Backoff Retry",
                "description": "Implement retry logic with exponential backoff and jitter to handle transient failures gracefully.",
                "implementation_effort": "low",
                "code": '''import time
import random
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=60.0):
    """Decorator: Exponential backoff retry with jitter"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    delay += random.uniform(0, delay * 0.1)  # jitter
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

# Usage:
@retry_with_backoff(max_retries=3, base_delay=1.0)
def call_external_service():
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()''',
            },
            "javascript": {
                "title": "Add Exponential Backoff Retry",
                "description": "Implement async retry logic with exponential backoff for API calls.",
                "implementation_effort": "low",
                "code": '''async function retryWithBackoff(fn, {
  maxRetries = 3,
  baseDelay = 1000,
  maxDelay = 60000
} = {}) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
      
      const delay = Math.min(
        baseDelay * Math.pow(2, attempt) + Math.random() * 1000,
        maxDelay
      );
      console.warn(`Attempt ${attempt + 1} failed: ${error.message}. Retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}

// Usage:
const data = await retryWithBackoff(
  () => fetch(url).then(r => r.json()),
  { maxRetries: 3 }
);''',
            },
        },
        "timeout": {
            "python": {
                "title": "Configure Proper Timeouts",
                "description": "Set explicit connection and read timeouts to prevent resource exhaustion from hanging connections.",
                "implementation_effort": "low",
                "code": '''import requests
from requests.adapters import HTTPAdapter

# Create session with proper timeouts
session = requests.Session()
adapter = HTTPAdapter(
    max_retries=3,
    pool_connections=10,
    pool_maxsize=10,
)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Always use explicit timeouts
CONNECT_TIMEOUT = 5   # seconds
READ_TIMEOUT = 30     # seconds

response = session.get(
    url,
    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
)''',
            },
            "javascript": {
                "title": "Configure Proper Timeouts",
                "description": "Set explicit timeouts with AbortController to prevent hanging requests.",
                "implementation_effort": "low",
                "code": '''async function fetchWithTimeout(url, options = {}, timeoutMs = 30000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeoutMs}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}''',
            },
        },
        "circuit_breaker": {
            "python": {
                "title": "Implement Circuit Breaker Pattern",
                "description": "Add circuit breaker to prevent cascading failures. The circuit opens after consecutive failures, allowing the system to recover.",
                "implementation_effort": "medium",
                "code": '''import time
from enum import Enum
from threading import Lock

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests  
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30, 
                 expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.lock = Lock()
    
    def call(self, func, *args, **kwargs):
        with self.lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN. Recovery in "
                        f"{self.recovery_timeout - (time.time() - self.last_failure_time):.0f}s"
                    )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        with self.lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

class CircuitBreakerOpenError(Exception):
    pass

# Usage:
payment_circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

def process_payment(order):
    return payment_circuit.call(payment_service.process, order)''',
            },
        },
        "fallback": {
            "python": {
                "title": "Add Fallback Strategy",
                "description": "Implement fallback mechanism to provide degraded but functional service when primary resource fails.",
                "implementation_effort": "medium",
                "code": '''from functools import wraps

def with_fallback(fallback_fn):
    """Decorator: Execute fallback function if primary fails"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Primary failed: {e}. Using fallback...")
                return fallback_fn(*args, **kwargs)
        return wrapper
    return decorator

# Example: Cache-based fallback
def get_from_cache(user_id):
    """Serve stale data from cache when DB is down"""
    return cache.get(f"user:{user_id}")

@with_fallback(get_from_cache)
def get_user(user_id):
    """Primary: Get user from database"""
    return db.query(User).get(user_id)''',
            },
        },
        "spof": {
            "python": {
                "title": "Eliminate Single Point of Failure",
                "description": "Add health checks, load balancing readiness, and redundancy mechanisms.",
                "implementation_effort": "high",
                "code": '''from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

# Health check endpoint for load balancer
@app.get("/health")
async def health_check():
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        checks["checks"]["database"] = "ok"
    except Exception:
        checks["checks"]["database"] = "failing"
        checks["status"] = "degraded"
    
    # Check external dependencies
    try:
        requests.get(external_url, timeout=2)
        checks["checks"]["external_api"] = "ok"
    except Exception:
        checks["checks"]["external_api"] = "failing"
        checks["status"] = "degraded"
    
    return checks

# Readiness probe
@app.get("/ready")
async def readiness():
    # Only report ready if critical dependencies are available
    return {"ready": True}''',
            },
        },
        "cascading": {
            "python": {
                "title": "Prevent Cascading Failures",
                "description": "Implement bulkhead pattern with circuit breakers to isolate failures and prevent cascade.",
                "implementation_effort": "high",
                "code": '''from concurrent.futures import ThreadPoolExecutor
import threading

class Bulkhead:
    """Limits concurrent access to prevent cascading failures"""
    
    def __init__(self, name, max_concurrent=10, max_wait=5):
        self.name = name
        self.semaphore = threading.Semaphore(max_concurrent)
        self.max_wait = max_wait
    
    def call(self, func, *args, **kwargs):
        acquired = self.semaphore.acquire(timeout=self.max_wait)
        if not acquired:
            raise BulkheadFullError(
                f"Bulkhead '{self.name}' is full. Max concurrent: {self.semaphore._value}"
            )
        try:
            return func(*args, **kwargs)
        finally:
            self.semaphore.release()

class BulkheadFullError(Exception):
    pass

# Usage: Isolate service calls
payment_bulkhead = Bulkhead("payment", max_concurrent=5)
inventory_bulkhead = Bulkhead("inventory", max_concurrent=10)

def process_order(order):
    payment = payment_bulkhead.call(payment_service.charge, order)
    inventory = inventory_bulkhead.call(inventory_service.reserve, order)
    return {"payment": payment, "inventory": inventory}''',
            },
        },
        "error_handling": {
            "python": {
                "title": "Improve Error Handling",
                "description": "Replace generic exception handling with specific error types and proper logging.",
                "implementation_effort": "low",
                "code": '''import logging
from requests.exceptions import (
    ConnectionError, Timeout, HTTPError
)

logger = logging.getLogger(__name__)

def call_service(url):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except ConnectionError:
        logger.error(f"Connection failed to {url}")
        raise ServiceUnavailableError(f"Cannot connect to {url}")
    except Timeout:
        logger.error(f"Request timed out for {url}")
        raise ServiceTimeoutError(f"Timeout calling {url}")
    except HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code} from {url}")
        if e.response.status_code >= 500:
            raise ServiceError(f"Server error from {url}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error calling {url}")
        raise''',
            },
        },
        "rate_limiting": {
            "python": {
                "title": "Add Rate Limiting",
                "description": "Implement rate limiting to protect API endpoints from overload and abuse.",
                "implementation_effort": "low",
                "code": '''from fastapi import FastAPI, Request, HTTPException
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        # Clean old entries
        self.requests[client_id] = [
            t for t in self.requests[client_id]
            if now - t < self.window
        ]
        
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        self.requests[client_id].append(now)
        return True

limiter = RateLimiter(max_requests=100, window_seconds=60)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return await call_next(request)''',
            },
        },
    }

    def __init__(self):
        self.client = None
        if HAS_OPENAI and settings.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception:
                pass

    def generate_fix(self, risk: Dict, code_context: str = "") -> Dict:
        """Generate a fix recommendation for a given risk."""
        category = risk.get("category", "error_handling")
        file_path = risk.get("file_path", "")
        
        # Determine language from file extension
        lang = self._detect_language(file_path)
        
        # Try LLM-based fix first
        if self.client and code_context:
            try:
                return self._llm_fix(risk, code_context, lang)
            except Exception as e:
                print(f"LLM fix generation failed: {e}")
        
        # Fall back to template-based fix
        return self._template_fix(risk, lang)

    def generate_fixes_batch(self, risks: List[Dict], repo_path: str = "") -> List[Dict]:
        """Generate fixes for multiple risks."""
        fixes = []
        for risk in risks:
            fix = self.generate_fix(risk)
            fixes.append(fix)
        return fixes

    def _template_fix(self, risk: Dict, lang: str) -> Dict:
        """Generate fix from templates."""
        category = risk.get("category", "error_handling")
        templates = self.FIX_TEMPLATES.get(category, {})
        
        # Get language-specific template or fall back to python
        template = templates.get(lang, templates.get("python", {}))
        
        if not template:
            return {
                "risk_id": risk["id"],
                "title": f"Fix: {risk['title']}",
                "description": risk.get("fix_suggestion", "Review and fix this reliability issue."),
                "original_code": risk.get("code_snippet", ""),
                "suggested_code": risk.get("fix_code", ""),
                "confidence": 0.6,
                "implementation_effort": "medium",
            }
        
        return {
            "risk_id": risk["id"],
            "title": template.get("title", f"Fix: {risk['title']}"),
            "description": template.get("description", risk.get("fix_suggestion", "")),
            "original_code": risk.get("code_snippet", ""),
            "suggested_code": template.get("code", ""),
            "confidence": 0.85,
            "implementation_effort": template.get("implementation_effort", "medium"),
        }

    def _llm_fix(self, risk: Dict, code_context: str, lang: str) -> Dict:
        """Use LLM to generate a contextual fix."""
        prompt = f"""You are an expert reliability engineer. Generate a specific fix for this code reliability issue.

RISK:
- Title: {risk['title']}
- Description: {risk['description']}
- Category: {risk['category']}
- Severity: {risk['severity']}
- File: {risk['file_path']}

CODE CONTEXT:
```{lang}
{code_context[:2000]}
```

PROBLEMATIC CODE:
```{lang}
{risk.get('code_snippet', 'N/A')}
```

Provide your response in this JSON format:
{{
  "title": "Short fix title",
  "description": "Detailed explanation of what to fix and why",
  "suggested_code": "The fixed code",
  "confidence": 0.0-1.0,
  "implementation_effort": "low|medium|high"
}}

Return ONLY valid JSON."""

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a reliability engineering AI. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith('```'):
            content = content.split('\n', 1)[1].rsplit('```', 1)[0]
        
        fix_data = json.loads(content)
        
        return {
            "risk_id": risk["id"],
            "title": fix_data.get("title", f"Fix: {risk['title']}"),
            "description": fix_data.get("description", ""),
            "original_code": risk.get("code_snippet", ""),
            "suggested_code": fix_data.get("suggested_code", ""),
            "confidence": fix_data.get("confidence", 0.7),
            "implementation_effort": fix_data.get("implementation_effort", "medium"),
        }

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        from pathlib import Path
        ext = Path(file_path).suffix.lower() if file_path else ".py"
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'javascript',
            '.jsx': 'javascript',
            '.tsx': 'javascript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
        }
        return lang_map.get(ext, 'python')
