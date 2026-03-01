"""
Cerebro Chaos - GitHub Import Service
Clones repositories and extracts file structure information.
"""
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from git import Repo, GitCommandError
from config import settings


class GitHubImportService:
    """Handles cloning GitHub repositories and extracting file metadata."""
    
    SUPPORTED_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
        '.rb', '.php', '.cs', '.cpp', '.c', '.h', '.hpp',
        '.yaml', '.yml', '.json', '.toml', '.env', '.cfg', '.ini',
        '.dockerfile', '.docker-compose', '.sh', '.bash',
        '.sql', '.graphql', '.proto',
    }
    
    IGNORE_DIRS = {
        'node_modules', '.git', '__pycache__', 'venv', '.venv',
        'dist', 'build', '.next', '.cache', 'coverage',
        '.idea', '.vscode', 'vendor', 'target',
    }

    def __init__(self):
        self.repos_dir = Path(settings.REPOS_DIR)
        self.repos_dir.mkdir(parents=True, exist_ok=True)

    def parse_url(self, url: str) -> Tuple[str, str]:
        """Extract owner and repo name from GitHub URL."""
        # Handle various GitHub URL formats
        patterns = [
            r'github\.com[:/]([^/]+)/([^/.]+)',
            r'github\.com[:/]([^/]+)/([^/.]+)\.git',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)
        
        # Fallback: try to extract from path
        parts = url.rstrip('/').split('/')
        if len(parts) >= 2:
            return parts[-2], parts[-1].replace('.git', '')
        
        raise ValueError(f"Cannot parse GitHub URL: {url}")

    def clone_repo(self, url: str, branch: str = "main") -> Dict:
        """Clone a GitHub repository and return metadata."""
        owner, name = self.parse_url(url)
        repo_id = str(uuid.uuid4())
        local_path = str(self.repos_dir / repo_id)
        
        try:
            # Clone the repository
            repo = Repo.clone_from(
                url, 
                local_path, 
                branch=branch,
                depth=1,  # Shallow clone for speed
            )
            
            # Count files and lines
            file_count, total_lines, language = self._analyze_repo_stats(local_path)
            
            return {
                "id": repo_id,
                "url": url,
                "name": name,
                "owner": owner,
                "branch": branch,
                "local_path": local_path,
                "language": language,
                "file_count": file_count,
                "total_lines": total_lines,
                "status": "cloning",
            }
        except GitCommandError as e:
            # Try with 'master' branch if 'main' fails
            if branch == "main":
                try:
                    repo = Repo.clone_from(url, local_path, branch="master", depth=1)
                    file_count, total_lines, language = self._analyze_repo_stats(local_path)
                    return {
                        "id": repo_id,
                        "url": url,
                        "name": name,
                        "owner": owner,
                        "branch": "master",
                        "local_path": local_path,
                        "language": language,
                        "file_count": file_count,
                        "total_lines": total_lines,
                        "status": "cloning",
                    }
                except Exception:
                    pass
            raise RuntimeError(f"Failed to clone repository: {str(e)}")

    def _analyze_repo_stats(self, repo_path: str) -> Tuple[int, int, str]:
        """Count files, lines, and detect primary language."""
        file_count = 0
        total_lines = 0
        lang_counts: Dict[str, int] = {}
        
        lang_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.jsx': 'React', '.tsx': 'React/TypeScript', '.java': 'Java',
            '.go': 'Go', '.rs': 'Rust', '.rb': 'Ruby', '.php': 'PHP',
            '.cs': 'C#', '.cpp': 'C++', '.c': 'C',
        }
        
        for root, dirs, files in os.walk(repo_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    file_count += 1
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            total_lines += lines
                            lang = lang_map.get(ext, 'Other')
                            lang_counts[lang] = lang_counts.get(lang, 0) + lines
                    except Exception:
                        pass
        
        # Primary language is the one with most lines
        primary_language = max(lang_counts, key=lang_counts.get) if lang_counts else "Unknown"
        
        return file_count, total_lines, primary_language

    def get_file_tree(self, repo_path: str) -> List[Dict]:
        """Get the file tree structure of a repository."""
        tree = []
        base = Path(repo_path)
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            rel_root = Path(root).relative_to(base)
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    file_path = str(rel_root / file)
                    tree.append({
                        "path": file_path,
                        "name": file,
                        "extension": ext,
                        "size": os.path.getsize(os.path.join(root, file)),
                    })
        
        return tree

    def read_file(self, repo_path: str, file_path: str) -> Optional[str]:
        """Read file contents from a cloned repository."""
        full_path = os.path.join(repo_path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return None

    def cleanup(self, repo_path: str):
        """Remove cloned repository."""
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)
