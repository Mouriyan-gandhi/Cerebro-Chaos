"""
Cerebro Chaos - Chaos Simulation Engine
Simulates various failure scenarios to test system resilience.
MVP version: Uses simulation/modeling rather than live infrastructure.
"""
import uuid
import time
import random
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional


class ChaosSimulationEngine:
    """
    Simulates chaos engineering scenarios:
    - Latency injection
    - Service failure
    - Resource exhaustion
    - Network partition
    - Database failure
    
    MVP: Uses statistical modeling based on code analysis to simulate
    failure outcomes without requiring actual infrastructure.
    """
    
    SIMULATION_TYPES = {
        "latency": {
            "name": "Latency Injection",
            "description": "Simulates increased latency on service calls",
            "default_config": {"delay_ms": 500, "jitter_ms": 100, "duration_s": 30},
        },
        "failure": {
            "name": "Service Failure",
            "description": "Simulates complete service failure/crash",
            "default_config": {"failure_rate": 1.0, "duration_s": 60},
        },
        "resource": {
            "name": "Resource Exhaustion",
            "description": "Simulates CPU/memory exhaustion",
            "default_config": {"cpu_percent": 90, "memory_percent": 85, "duration_s": 30},
        },
        "network": {
            "name": "Network Partition",
            "description": "Simulates network connectivity issues",
            "default_config": {"packet_loss": 0.5, "duration_s": 30},
        },
        "database": {
            "name": "Database Failure",
            "description": "Simulates database unavailability",
            "default_config": {"failure_type": "connection_refused", "duration_s": 30},
        },
    }

    def __init__(self):
        self.active_tests = {}

    def create_simulation(
        self, 
        test_type: str, 
        risk: Dict, 
        services: List[Dict],
        dependency_graph: Dict,
        config: Dict = None,
    ) -> Dict:
        """Create a chaos simulation based on risk and system analysis."""
        sim_type = self.SIMULATION_TYPES.get(test_type, self.SIMULATION_TYPES["latency"])
        
        sim_config = {**sim_type["default_config"]}
        if config:
            sim_config.update(config)
        
        test_id = str(uuid.uuid4())
        
        simulation = {
            "id": test_id,
            "test_type": test_type,
            "target_service": risk.get("file_path", "unknown"),
            "status": "pending",
            "config": sim_config,
            "risk": risk,
            "baseline_latency": None,
            "chaos_latency": None,
            "error_rate_before": None,
            "error_rate_after": None,
            "cascading_failures": [],
            "result_summary": None,
            "failure_probability": None,
            "started_at": None,
            "completed_at": None,
        }
        
        self.active_tests[test_id] = simulation
        return simulation

    def run_simulation(
        self, 
        test_id: str,
        services: List[Dict],
        dependency_graph: Dict,
        reliability_indicators: Dict,
    ) -> Dict:
        """
        Run a chaos simulation.
        MVP: Uses statistical modeling to predict outcomes.
        """
        simulation = self.active_tests.get(test_id)
        if not simulation:
            raise ValueError(f"Simulation {test_id} not found")
        
        simulation["status"] = "running"
        simulation["started_at"] = datetime.utcnow().isoformat()
        
        risk = simulation["risk"]
        test_type = simulation["test_type"]
        config = simulation["config"]
        
        # Simulate based on test type
        if test_type == "latency":
            result = self._simulate_latency(risk, services, dependency_graph, reliability_indicators, config)
        elif test_type == "failure":
            result = self._simulate_failure(risk, services, dependency_graph, reliability_indicators, config)
        elif test_type == "resource":
            result = self._simulate_resource_exhaustion(risk, services, dependency_graph, config)
        elif test_type == "network":
            result = self._simulate_network_partition(risk, services, dependency_graph, reliability_indicators, config)
        elif test_type == "database":
            result = self._simulate_database_failure(risk, services, dependency_graph, reliability_indicators, config)
        else:
            result = self._simulate_generic(risk, config)
        
        # Update simulation with results
        simulation.update(result)
        simulation["status"] = "completed"
        simulation["completed_at"] = datetime.utcnow().isoformat()
        
        return simulation

    def _simulate_latency(
        self, risk: Dict, services: List[Dict], 
        graph: Dict, indicators: Dict, config: Dict
    ) -> Dict:
        """Simulate latency injection and predict cascading effects."""
        delay_ms = config.get("delay_ms", 500)
        
        # Baseline: estimate normal latency based on service type
        target_service = risk.get("file_path", "")
        service = next((s for s in services if s.get("path") == target_service), None)
        
        baseline = self._estimate_baseline_latency(service)
        
        # Calculate chaos impact
        has_timeout = any(
            t["file"] == target_service 
            for t in indicators.get("timeout_configs", [])
        )
        has_retry = any(
            r["file"] == target_service 
            for r in indicators.get("retry_patterns", [])
        )
        has_circuit_breaker = any(
            c["file"] == target_service 
            for c in indicators.get("circuit_breakers", [])
        )
        
        # Calculate chaos latency
        chaos_latency = baseline + delay_ms
        
        # Without timeout, latency can grow unbounded
        if not has_timeout:
            chaos_latency *= random.uniform(2.0, 5.0)
        
        # Without retry, single failures become permanent
        if has_retry:
            # Retries add latency but improve reliability
            chaos_latency *= random.uniform(1.5, 3.0)  # retry overhead
            error_rate = random.uniform(0.05, 0.15)
        else:
            error_rate = random.uniform(0.30, 0.70)
        
        # With circuit breaker, failures are contained
        if has_circuit_breaker:
            error_rate *= 0.3  # Significantly reduced
        
        # Detect cascading failures
        cascading = self._detect_cascading_failures(
            target_service, graph, services, indicators
        )
        
        # Calculate failure probability
        failure_prob = self._calculate_failure_probability(
            risk, has_timeout, has_retry, has_circuit_breaker, error_rate
        )
        
        return {
            "baseline_latency": round(baseline, 2),
            "chaos_latency": round(chaos_latency, 2),
            "error_rate_before": round(random.uniform(0.001, 0.01), 4),
            "error_rate_after": round(error_rate, 4),
            "cascading_failures": cascading,
            "failure_probability": round(failure_prob, 2),
            "result_summary": self._generate_summary(
                "latency", baseline, chaos_latency, error_rate, 
                cascading, failure_prob, has_timeout, has_retry, has_circuit_breaker
            ),
        }

    def _simulate_failure(
        self, risk: Dict, services: List[Dict],
        graph: Dict, indicators: Dict, config: Dict
    ) -> Dict:
        """Simulate complete service failure."""
        target_service = risk.get("file_path", "")
        
        has_fallback = any(
            f["file"] == target_service 
            for f in indicators.get("fallbacks", [])
        )
        has_circuit_breaker = any(
            c["file"] == target_service 
            for c in indicators.get("circuit_breakers", [])
        )
        
        baseline = self._estimate_baseline_latency(
            next((s for s in services if s.get("path") == target_service), None)
        )
        
        # Complete failure
        if has_fallback:
            chaos_latency = baseline * random.uniform(1.2, 2.0)
            error_rate = random.uniform(0.05, 0.20)
        else:
            chaos_latency = 30000  # 30s timeout
            error_rate = random.uniform(0.80, 1.0)
        
        if has_circuit_breaker:
            chaos_latency = min(chaos_latency, baseline * 3)
            error_rate *= 0.5
        
        cascading = self._detect_cascading_failures(
            target_service, graph, services, indicators
        )
        
        failure_prob = min(0.99, error_rate * 1.2)
        
        return {
            "baseline_latency": round(baseline, 2),
            "chaos_latency": round(chaos_latency, 2),
            "error_rate_before": round(random.uniform(0.001, 0.01), 4),
            "error_rate_after": round(error_rate, 4),
            "cascading_failures": cascading,
            "failure_probability": round(failure_prob, 2),
            "result_summary": self._generate_summary(
                "failure", baseline, chaos_latency, error_rate,
                cascading, failure_prob, False, False, has_circuit_breaker
            ),
        }

    def _simulate_resource_exhaustion(
        self, risk: Dict, services: List[Dict], 
        graph: Dict, config: Dict
    ) -> Dict:
        """Simulate resource exhaustion (CPU/memory)."""
        baseline = random.uniform(50, 200)
        cpu_percent = config.get("cpu_percent", 90)
        
        # High CPU causes latency spike
        latency_multiplier = 1 + (cpu_percent / 100) * 5
        chaos_latency = baseline * latency_multiplier
        error_rate = (cpu_percent / 100) * random.uniform(0.3, 0.7)
        
        return {
            "baseline_latency": round(baseline, 2),
            "chaos_latency": round(chaos_latency, 2),
            "error_rate_before": round(random.uniform(0.001, 0.01), 4),
            "error_rate_after": round(error_rate, 4),
            "cascading_failures": [],
            "failure_probability": round(min(0.99, error_rate * 1.1), 2),
            "result_summary": f"Resource exhaustion at {cpu_percent}% CPU caused {round(latency_multiplier, 1)}x latency increase and {round(error_rate*100, 1)}% error rate.",
        }

    def _simulate_network_partition(
        self, risk: Dict, services: List[Dict],
        graph: Dict, indicators: Dict, config: Dict
    ) -> Dict:
        """Simulate network partition between services."""
        packet_loss = config.get("packet_loss", 0.5)
        baseline = random.uniform(50, 200)
        
        has_retry = any(
            r["file"] == risk.get("file_path", "")
            for r in indicators.get("retry_patterns", [])
        )
        
        if has_retry:
            chaos_latency = baseline * (1 + packet_loss * 3)
            error_rate = packet_loss * random.uniform(0.3, 0.5)
        else:
            chaos_latency = baseline * (1 + packet_loss * 10)
            error_rate = packet_loss * random.uniform(0.7, 0.95)
        
        cascading = self._detect_cascading_failures(
            risk.get("file_path", ""), graph, services, indicators
        )
        
        return {
            "baseline_latency": round(baseline, 2),
            "chaos_latency": round(chaos_latency, 2),
            "error_rate_before": round(random.uniform(0.001, 0.01), 4),
            "error_rate_after": round(error_rate, 4),
            "cascading_failures": cascading,
            "failure_probability": round(min(0.99, error_rate * 1.2), 2),
            "result_summary": f"Network partition with {int(packet_loss*100)}% packet loss. {'Retry logic helped contain damage.' if has_retry else 'No retry logic - failures amplified.'}",
        }

    def _simulate_database_failure(
        self, risk: Dict, services: List[Dict],
        graph: Dict, indicators: Dict, config: Dict
    ) -> Dict:
        """Simulate database unavailability."""
        baseline = random.uniform(20, 100)
        
        has_fallback = any(
            f["file"] == risk.get("file_path", "")
            for f in indicators.get("fallbacks", [])
        )
        
        if has_fallback:
            chaos_latency = baseline * random.uniform(1.1, 1.5)
            error_rate = random.uniform(0.05, 0.15)
            summary = "Database failure handled by fallback mechanism. Degraded but operational."
        else:
            chaos_latency = 30000  # Connection timeout
            error_rate = random.uniform(0.85, 0.99)
            summary = "Database failure caused complete service outage. No fallback mechanism detected."
        
        cascading = self._detect_cascading_failures(
            risk.get("file_path", ""), graph, services, indicators
        )
        
        return {
            "baseline_latency": round(baseline, 2),
            "chaos_latency": round(chaos_latency, 2),
            "error_rate_before": round(random.uniform(0.001, 0.01), 4),
            "error_rate_after": round(error_rate, 4),
            "cascading_failures": cascading,
            "failure_probability": round(min(0.99, error_rate), 2),
            "result_summary": summary,
        }

    def _simulate_generic(self, risk: Dict, config: Dict) -> Dict:
        """Generic failure simulation."""
        baseline = random.uniform(50, 200)
        return {
            "baseline_latency": round(baseline, 2),
            "chaos_latency": round(baseline * random.uniform(3, 10), 2),
            "error_rate_before": round(random.uniform(0.001, 0.01), 4),
            "error_rate_after": round(random.uniform(0.3, 0.7), 4),
            "cascading_failures": [],
            "failure_probability": round(risk.get("failure_probability", 0.5), 2),
            "result_summary": "Generic failure simulation completed.",
        }

    def _estimate_baseline_latency(self, service: Optional[Dict]) -> float:
        """Estimate baseline latency for a service type."""
        if not service:
            return random.uniform(50, 200)
        
        service_type = service.get("service_type", "api")
        latency_map = {
            "api": random.uniform(50, 150),
            "database": random.uniform(5, 50),
            "cache": random.uniform(1, 10),
            "queue": random.uniform(10, 100),
            "external": random.uniform(100, 500),
            "gateway": random.uniform(20, 80),
        }
        return latency_map.get(service_type, random.uniform(50, 200))

    def _detect_cascading_failures(
        self, target: str, graph: Dict, 
        services: List[Dict], indicators: Dict
    ) -> List[str]:
        """Detect which services would be affected by a cascading failure."""
        cascading = []
        edges = graph.get("edges", [])
        nodes = {n["id"]: n for n in graph.get("nodes", [])}
        
        # Find services that depend on the target
        target_name = Path(target).stem if '/' in target or '\\' in target else target
        
        affected = set()
        queue = [target_name]
        
        while queue:
            current = queue.pop(0)
            for edge in edges:
                if edge.get("target") == current and edge.get("source") not in affected:
                    affected.add(edge["source"])
                    queue.append(edge["source"])
        
        for service_name in affected:
            # Check if affected service has its own resilience
            service = next((s for s in services if s["name"] == service_name), None)
            if service:
                has_protection = any(
                    c["file"] == service.get("path", "")
                    for c in indicators.get("circuit_breakers", [])
                )
                if not has_protection:
                    cascading.append(
                        f"{service_name}: No circuit breaker, will fail when '{target_name}' fails"
                    )
                else:
                    cascading.append(
                        f"{service_name}: Circuit breaker may protect, but degraded performance expected"
                    )
        
        return cascading

    def _calculate_failure_probability(
        self, risk: Dict, has_timeout: bool, 
        has_retry: bool, has_circuit_breaker: bool,
        base_error_rate: float
    ) -> float:
        """Calculate overall failure probability based on resilience patterns."""
        prob = risk.get("failure_probability", 0.5)
        
        if has_timeout:
            prob *= 0.7
        if has_retry:
            prob *= 0.5
        if has_circuit_breaker:
            prob *= 0.4
        
        # Factor in error rate
        prob = (prob + base_error_rate) / 2
        
        return min(0.99, max(0.01, prob))

    def _generate_summary(
        self, test_type: str, baseline: float, chaos_latency: float,
        error_rate: float, cascading: List[str], failure_prob: float,
        has_timeout: bool, has_retry: bool, has_circuit_breaker: bool
    ) -> str:
        """Generate human-readable summary of simulation results."""
        latency_increase = ((chaos_latency - baseline) / baseline) * 100
        
        lines = [
            f"**{test_type.title()} Simulation Results:**",
            f"",
            f"• Latency: {baseline:.0f}ms → {chaos_latency:.0f}ms ({latency_increase:.0f}% increase)",
            f"• Error Rate: {error_rate*100:.1f}%",
            f"• Failure Probability: {failure_prob*100:.0f}%",
            f"",
            "**Resilience Patterns:**",
            f"  ✗ Timeout: {'✓ Present' if has_timeout else '✗ Missing'}",
            f"  ✗ Retry: {'✓ Present' if has_retry else '✗ Missing'}",
            f"  ✗ Circuit Breaker: {'✓ Present' if has_circuit_breaker else '✗ Missing'}",
        ]
        
        if cascading:
            lines.append(f"")
            lines.append(f"**⚠ Cascading Failures ({len(cascading)}):**")
            for c in cascading[:5]:
                lines.append(f"  • {c}")
        
        return "\n".join(lines)


# Import Path for file path handling  
from pathlib import Path
