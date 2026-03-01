"""
Cerebro Chaos - Code Analysis Engine
Parses code to extract services, APIs, databases, dependencies and builds a dependency graph.
"""
import ast
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx

from github_import.service import GitHubImportService


class CodeAnalysisEngine:
    """
    Analyzes codebase to extract:
    - Services and their types
    - API endpoints
    - Database connections
    - External dependencies  
    - Dependency graph
    """

    # Patterns to detect different service types
    PATTERNS = {
        "api_endpoint": {
            "python": [
                r'@app\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)',
                r'@router\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)',
                r'@api_view\s*\(\[([^\]]+)',
                r'path\s*\(["\']([^"\']+)',
            ],
            "javascript": [
                r'app\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)',
                r'router\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)',
            ],
        },
        "database": {
            "connection_strings": [
                r'(postgresql|mysql|mongodb|redis|sqlite|dynamodb)://[^\s"\']+',
                r'(DATABASE_URL|DB_HOST|MONGO_URI|REDIS_URL)',
                r'(create_engine|connect|MongoClient|Redis)\s*\(',
                r'(sequelize|mongoose|prisma|typeorm|sqlalchemy)',
            ],
        },
        "external_api": [
            r'(requests\.(get|post|put|delete)|fetch\s*\(|axios\.(get|post|put|delete)|httpx)',
            r'(https?://[^\s"\']+api[^\s"\']*)',
        ],
        "queue_broker": [
            r'(celery|rabbitmq|kafka|sqs|redis\.Queue|bull|BullMQ)',
            r'(pika\.connect|KafkaProducer|KafkaConsumer)',
        ],
        "retry_pattern": [
            r'(retry|retries|max_retries|retry_count|backoff)',
            r'(tenacity|retrying|backoff\.expo)',
            r'for\s+\w+\s+in\s+range\s*\(\s*\d+\s*\).*?(request|call|connect)',
        ],
        "timeout_pattern": [
            r'timeout\s*[=:]\s*(\d+)',
            r'(connect_timeout|read_timeout|write_timeout)',
            r'setTimeout|setInterval',
        ],
        "circuit_breaker": [
            r'(circuit.?breaker|CircuitBreaker|pybreaker|opossum)',
        ],
        "error_handling": [
            r'(try\s*:|try\s*\{)',
            r'(except|catch)\s*[\(:]',
            r'(\.catch\s*\(|\.on\s*\(["\']error)',
        ],
        "fallback": [
            r'(fallback|failover|failsafe|default_value|cache\.get)',
        ],
    }

    def __init__(self):
        self.import_service = GitHubImportService()

    def analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        Full analysis of a repository.
        Returns services, dependencies, and dependency graph.
        """
        file_tree = self.import_service.get_file_tree(repo_path)
        
        services = []
        all_endpoints = []
        all_dependencies = []
        reliability_indicators = {
            "retry_patterns": [],
            "timeout_configs": [],
            "circuit_breakers": [],
            "error_handling": [],
            "fallbacks": [],
        }
        
        # Analyze each file
        for file_info in file_tree:
            content = self.import_service.read_file(repo_path, file_info["path"])
            if not content:
                continue
            
            ext = file_info["extension"]
            file_analysis = self._analyze_file(file_info["path"], content, ext)
            
            if file_analysis.get("is_service"):
                services.append(file_analysis)
            
            all_endpoints.extend(file_analysis.get("endpoints", []))
            all_dependencies.extend(file_analysis.get("dependencies", []))
            
            # Collect reliability indicators
            for key in reliability_indicators:
                reliability_indicators[key].extend(
                    file_analysis.get(key, [])
                )
        
        # Build dependency graph
        graph = self._build_dependency_graph(services, all_dependencies)
        
        # Detect service types
        services = self._classify_services(services)
        
        return {
            "services": services,
            "endpoints": all_endpoints,
            "dependencies": all_dependencies,
            "dependency_graph": graph,
            "reliability_indicators": reliability_indicators,
            "file_count": len(file_tree),
        }

    def _analyze_file(self, file_path: str, content: str, ext: str) -> Dict[str, Any]:
        """Analyze a single file for services, endpoints, and patterns."""
        result = {
            "path": file_path,
            "name": Path(file_path).stem,
            "is_service": False,
            "service_type": None,
            "endpoints": [],
            "dependencies": [],
            "imports": [],
            "retry_patterns": [],
            "timeout_configs": [],
            "circuit_breakers": [],
            "error_handling": [],
            "fallbacks": [],
            "db_connections": [],
            "external_calls": [],
        }
        
        # Parse Python files with AST
        if ext == '.py':
            result = self._analyze_python(file_path, content, result)
        elif ext in ('.js', '.ts', '.jsx', '.tsx'):
            result = self._analyze_javascript(file_path, content, result)
        else:
            result = self._analyze_generic(file_path, content, result)
        
        # Detect endpoints
        result["endpoints"] = self._find_endpoints(content, ext, file_path)
        
        # Detect reliability patterns
        result["retry_patterns"] = self._find_patterns(content, self.PATTERNS["retry_pattern"], file_path)
        result["timeout_configs"] = self._find_patterns(content, self.PATTERNS["timeout_pattern"], file_path)
        result["circuit_breakers"] = self._find_patterns(content, self.PATTERNS["circuit_breaker"], file_path)
        result["error_handling"] = self._find_patterns(content, self.PATTERNS["error_handling"], file_path)
        result["fallbacks"] = self._find_patterns(content, self.PATTERNS["fallback"], file_path)
        result["db_connections"] = self._find_patterns(content, self.PATTERNS["database"]["connection_strings"], file_path)
        result["external_calls"] = self._find_patterns(content, self.PATTERNS["external_api"], file_path)
        
        # Determine if this file is a service
        if (result["endpoints"] or result["db_connections"] or 
            result["external_calls"] or self._is_service_file(file_path)):
            result["is_service"] = True
        
        return result

    def _analyze_python(self, file_path: str, content: str, result: Dict) -> Dict:
        """Deep analysis of Python files using AST."""
        try:
            tree = ast.parse(content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result["imports"].append(node.module)
                        result["dependencies"].append({
                            "from": file_path,
                            "to": node.module,
                            "type": "import",
                        })
            
            # Detect classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a service-like class
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id in (
                            'APIRouter', 'Blueprint', 'View', 'ViewSet', 'Resource'
                        ):
                            result["is_service"] = True
                            result["service_type"] = "api"
                
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # Check for decorator-based endpoints
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Attribute):
                                if decorator.func.attr in ('get', 'post', 'put', 'delete', 'patch'):
                                    result["is_service"] = True
                                    result["service_type"] = "api"
        except SyntaxError:
            pass
        
        return result

    def _analyze_javascript(self, file_path: str, content: str, result: Dict) -> Dict:
        """Analyze JavaScript/TypeScript files using regex patterns."""
        # Extract imports
        import_patterns = [
            r'import\s+.*?\s+from\s+["\']([^"\']+)',
            r'require\s*\(["\']([^"\']+)',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                result["imports"].append(match)
                if not match.startswith('.'):
                    continue
                result["dependencies"].append({
                    "from": file_path,
                    "to": match,
                    "type": "import",
                })
        
        # Detect Express/Fastify routes
        route_pattern = r'(app|router)\.(get|post|put|delete|patch)\s*\('
        if re.search(route_pattern, content):
            result["is_service"] = True
            result["service_type"] = "api"
        
        return result

    def _analyze_generic(self, file_path: str, content: str, result: Dict) -> Dict:
        """Generic file analysis for config files, dockerfiles, etc."""
        # Docker compose analysis
        if 'docker-compose' in file_path.lower() or file_path.endswith(('.yaml', '.yml')):
            if 'services:' in content:
                result["is_service"] = True
                result["service_type"] = "infrastructure"
        
        return result

    def _find_endpoints(self, content: str, ext: str, file_path: str) -> List[Dict]:
        """Find API endpoints in code."""
        endpoints = []
        
        lang = "python" if ext == '.py' else "javascript"
        patterns = self.PATTERNS["api_endpoint"].get(lang, [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                groups = match.groups()
                method = groups[0].upper() if len(groups) > 1 else "GET"
                path = groups[-1] if groups else ""
                
                endpoints.append({
                    "method": method,
                    "path": path,
                    "file": file_path,
                    "line": content[:match.start()].count('\n') + 1,
                })
        
        return endpoints

    def _find_patterns(self, content: str, patterns: List[str], file_path: str) -> List[Dict]:
        """Find regex patterns in code and return with line info."""
        results = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                # Get the full line
                lines = content.split('\n')
                line_content = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                
                results.append({
                    "pattern": pattern,
                    "match": match.group(),
                    "file": file_path,
                    "line": line_num,
                    "line_content": line_content,
                })
        
        return results

    def _is_service_file(self, file_path: str) -> bool:
        """Determine if a file is likely a service based on its path/name."""
        service_indicators = [
            'service', 'server', 'app', 'main', 'api', 'route',
            'controller', 'handler', 'middleware', 'gateway',
            'worker', 'consumer', 'producer',
        ]
        name = Path(file_path).stem.lower()
        return any(indicator in name for indicator in service_indicators)

    def _classify_services(self, services: List[Dict]) -> List[Dict]:
        """Classify services into types based on their characteristics."""
        for service in services:
            if service.get("service_type"):
                continue
            
            path = service["path"].lower()
            name = service["name"].lower()
            
            if any(x in name for x in ['db', 'database', 'model', 'migration']):
                service["service_type"] = "database"
            elif any(x in name for x in ['queue', 'worker', 'consumer', 'celery', 'task']):
                service["service_type"] = "queue"
            elif any(x in name for x in ['cache', 'redis']):
                service["service_type"] = "cache"
            elif any(x in name for x in ['gateway', 'proxy', 'nginx']):
                service["service_type"] = "gateway"
            elif service.get("external_calls"):
                service["service_type"] = "external"
            elif service.get("endpoints"):
                service["service_type"] = "api"
            else:
                service["service_type"] = "internal"
        
        return services

    def _build_dependency_graph(self, services: List[Dict], dependencies: List[Dict]) -> Dict:
        """Build a dependency graph from services and their dependencies."""
        G = nx.DiGraph()
        
        # Add service nodes
        for service in services:
            G.add_node(service["name"], **{
                "type": service.get("service_type", "unknown"),
                "path": service["path"],
                "endpoints": len(service.get("endpoints", [])),
            })
        
        # Add dependency edges
        for dep in dependencies:
            from_name = Path(dep["from"]).stem
            to_name = dep["to"].split('.')[-1] if '.' in dep["to"] else dep["to"]
            
            if from_name in G.nodes and to_name in G.nodes:
                G.add_edge(from_name, to_name, type=dep.get("type", "depends"))
            elif from_name in G.nodes:
                G.add_node(to_name, type="external")
                G.add_edge(from_name, to_name, type=dep.get("type", "depends"))
        
        # Convert to serializable format
        nodes = []
        for node, data in G.nodes(data=True):
            nodes.append({
                "id": node,
                "label": node,
                **data,
            })
        
        edges = []
        for u, v, data in G.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                **data,
            })
        
        return {"nodes": nodes, "edges": edges}
