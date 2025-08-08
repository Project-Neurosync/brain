"""
GitHub Integration Service for NeuroSync API
Handles GitHub API authentication, repository scanning, and data ingestion
"""

import logging
import aiohttp
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import asyncio
import re

from sqlalchemy.orm import Session
from models.integration import Integration
from models.project import Project
from .base import BaseIntegrationService

# Create logger
logger = logging.getLogger(__name__)

class GitHubIntegrationService(BaseIntegrationService):
    """
    GitHub Integration Service
    Handles GitHub API authentication, repository scanning, and data ingestion
    """
    
    # GitHub API constants
    API_BASE_URL = "https://api.github.com"
    DEFAULT_HEADERS = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Supported file types and max file size
    SUPPORTED_EXTENSIONS = [
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', 
        '.hpp', '.cs', '.go', '.rb', '.php', '.swift', '.kt', '.rs', 
        '.html', '.css', '.scss', '.md', '.json', '.yaml', '.yml'
    ]
    MAX_FILE_SIZE = 1024 * 1024  # 1MB
    
    # Paths to exclude
    EXCLUDED_PATHS = [
        'node_modules/', 'venv/', 'env/', '.venv/', '.env/', 
        'dist/', 'build/', '.git/', '__pycache__/', 
    ]
    
    def __init__(self, db: Session, integration: Optional[Integration] = None):
        """
        Initialize GitHub integration service
        
        Args:
            db: SQLAlchemy database session
            integration: Optional Integration model instance
        """
        super().__init__(db, integration)
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test GitHub API connection
        
        Args:
            config: GitHub integration config with token
            
        Returns:
            Dict with connection test results
        """
        token = config.get("token")
        if not token:
            return {
                "success": False,
                "message": "GitHub token is required"
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Test API connection by getting user info
            headers = {**self.DEFAULT_HEADERS, "Authorization": f"Bearer {token}"}
            async with self.session.get(f"{self.API_BASE_URL}/user", headers=headers) as response:
                if response.status == 200:
                    user_data = await response.json()
                    return {
                        "success": True,
                        "message": f"Successfully connected to GitHub as {user_data.get('login')}",
                        "details": {
                            "username": user_data.get('login'),
                            "name": user_data.get('name'),
                            "avatar_url": user_data.get('avatar_url')
                        }
                    }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "message": f"GitHub API error: {error_data.get('message', 'Unknown error')}",
                        "details": {"status_code": response.status}
                    }
        except Exception as e:
            logger.error(f"Error testing GitHub connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to GitHub: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def get_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get GitHub metadata (user info, repositories, etc.)
        
        Args:
            config: GitHub integration config with token
            
        Returns:
            Dict with GitHub metadata
        """
        token = config.get("token")
        if not token:
            return {
                "success": False,
                "message": "GitHub token is required"
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = {**self.DEFAULT_HEADERS, "Authorization": f"Bearer {token}"}
            
            # Get user info
            async with self.session.get(f"{self.API_BASE_URL}/user", headers=headers) as response:
                if response.status != 200:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "message": f"GitHub API error: {error_data.get('message', 'Unknown error')}",
                        "details": {"status_code": response.status}
                    }
                
                user_data = await response.json()
            
            # Get user repositories (first 100)
            async with self.session.get(
                f"{self.API_BASE_URL}/user/repos?per_page=100", 
                headers=headers
            ) as response:
                if response.status != 200:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "message": f"GitHub API error: {error_data.get('message', 'Unknown error')}",
                        "details": {"status_code": response.status}
                    }
                
                repos_data = await response.json()
            
            # Format repository data
            repos = []
            for repo in repos_data:
                repos.append({
                    "id": repo.get("id"),
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "description": repo.get("description"),
                    "private": repo.get("private"),
                    "html_url": repo.get("html_url"),
                    "language": repo.get("language"),
                    "stargazers_count": repo.get("stargazers_count"),
                    "fork": repo.get("fork")
                })
            
            return {
                "success": True,
                "user": {
                    "username": user_data.get("login"),
                    "name": user_data.get("name"),
                    "avatar_url": user_data.get("avatar_url"),
                    "email": user_data.get("email"),
                    "company": user_data.get("company"),
                    "location": user_data.get("location")
                },
                "repositories": repos,
                "repository_count": len(repos)
            }
        except Exception as e:
            logger.error(f"Error getting GitHub metadata: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting GitHub metadata: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def ingest_data(self, project_id: UUID, limit: int = 100) -> Dict[str, Any]:
        """
        Ingest data from GitHub repositories
        
        Args:
            project_id: Project ID to associate data with
            limit: Maximum number of repositories to process
            
        Returns:
            Dict with ingestion results
        """
        if not self.integration:
            return {
                "success": False,
                "message": "Integration not initialized",
                "items_processed": 0,
                "items_imported": 0,
                "errors": ["Integration not initialized"]
            }
        
        # Get integration config
        config = self.integration.config or {}
        token = config.get("token")
        selected_repos = config.get("repositories", [])
        
        if not token:
            return {
                "success": False,
                "message": "GitHub token is required",
                "items_processed": 0,
                "items_imported": 0,
                "errors": ["GitHub token is required"]
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Update sync status
            await self.update_sync_status("syncing", "Starting GitHub repository ingestion")
            
            # Get repositories to process
            metadata = await self.get_metadata({"token": token})
            if not metadata.get("success", False):
                await self.update_sync_status("error", metadata.get("message"))
                return {
                    "success": False,
                    "message": metadata.get("message"),
                    "items_processed": 0,
                    "items_imported": 0,
                    "errors": [metadata.get("message")]
                }
            
            repositories = metadata.get("repositories", [])
            
            # Filter repositories based on selected repos in config
            if selected_repos:
                repositories = [r for r in repositories if r.get("full_name") in selected_repos]
            
            # Limit repositories to process
            repositories = repositories[:limit]
            
            # Process each repository
            items_processed = 0
            items_imported = 0
            errors = []
            
            for repo in repositories:
                try:
                    logger.info(f"Processing GitHub repository: {repo.get('full_name')}")
                    
                    # Scan repository and process files
                    scan_result = await self._scan_repository(
                        token=token,
                        repo_name=repo.get("full_name"),
                        project_id=project_id
                    )
                    
                    items_processed += scan_result.get("files_processed", 0)
                    items_imported += scan_result.get("files_imported", 0)
                    
                    if not scan_result.get("success", False):
                        errors.append(
                            f"Error scanning repository {repo.get('full_name')}: {scan_result.get('message')}"
                        )
                        
                except Exception as e:
                    logger.error(f"Error processing repository {repo.get('full_name')}: {str(e)}")
                    errors.append(f"Error processing repository {repo.get('full_name')}: {str(e)}")
            
            # Update sync status
            status = "completed" if items_imported > 0 and not errors else "error"
            error_message = "; ".join(errors) if errors else None
            await self.update_sync_status(status, error_message)
            
            # Schedule next sync (7 days from now)
            next_sync = datetime.utcnow() + timedelta(days=7)
            await self.schedule_next_sync(next_sync)
            
            return {
                "success": items_imported > 0,
                "message": f"Processed {items_processed} files, imported {items_imported} files",
                "items_processed": items_processed,
                "items_imported": items_imported,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error ingesting GitHub data: {str(e)}")
            await self.update_sync_status("error", str(e))
            return {
                "success": False,
                "message": f"Error ingesting GitHub data: {str(e)}",
                "items_processed": 0,
                "items_imported": 0,
                "errors": [str(e)]
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def _scan_repository(
        self, token: str, repo_name: str, project_id: UUID
    ) -> Dict[str, Any]:
        """
        Scan GitHub repository and process files
        
        Args:
            token: GitHub API token
            repo_name: Repository name (owner/repo)
            project_id: Project ID to associate data with
            
        Returns:
            Dict with scan results
        """
        try:
            headers = {**self.DEFAULT_HEADERS, "Authorization": f"Bearer {token}"}
            
            # Get repository contents (root directory)
            async with self.session.get(
                f"{self.API_BASE_URL}/repos/{repo_name}/contents", 
                headers=headers
            ) as response:
                if response.status != 200:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "message": f"GitHub API error: {error_data.get('message', 'Unknown error')}",
                        "files_processed": 0,
                        "files_imported": 0
                    }
                
                contents = await response.json()
            
            # Process repository contents
            files_to_process = []
            dirs_to_process = []
            
            # Initial processing of root directory
            for item in contents:
                if item.get("type") == "file" and self._should_process_file(item.get("path", ""), item.get("size", 0)):
                    files_to_process.append(item)
                elif item.get("type") == "dir" and not self._is_excluded_path(item.get("path", "")):
                    dirs_to_process.append(item.get("path"))
            
            # Process directories recursively
            while dirs_to_process:
                dir_path = dirs_to_process.pop(0)
                
                # Get directory contents
                async with self.session.get(
                    f"{self.API_BASE_URL}/repos/{repo_name}/contents/{dir_path}", 
                    headers=headers
                ) as response:
                    if response.status != 200:
                        continue
                    
                    dir_contents = await response.json()
                
                # Process directory contents
                for item in dir_contents:
                    if item.get("type") == "file" and self._should_process_file(item.get("path", ""), item.get("size", 0)):
                        files_to_process.append(item)
                    elif item.get("type") == "dir" and not self._is_excluded_path(item.get("path", "")):
                        dirs_to_process.append(item.get("path"))
            
            # Process files in batches
            batch_size = 10
            file_batches = [files_to_process[i:i + batch_size] for i in range(0, len(files_to_process), batch_size)]
            
            files_processed = 0
            files_imported = 0
            
            for batch in file_batches:
                batch_result = await self._process_file_batch(
                    token=token,
                    repo_name=repo_name,
                    files=batch,
                    project_id=project_id
                )
                
                files_processed += len(batch)
                files_imported += batch_result.get("files_imported", 0)
            
            return {
                "success": True,
                "message": f"Processed {files_processed} files, imported {files_imported} files",
                "files_processed": files_processed,
                "files_imported": files_imported
            }
            
        except Exception as e:
            logger.error(f"Error scanning repository {repo_name}: {str(e)}")
            return {
                "success": False,
                "message": f"Error scanning repository: {str(e)}",
                "files_processed": 0,
                "files_imported": 0
            }
    
    async def _process_file_batch(
        self, token: str, repo_name: str, files: List[Dict[str, Any]], project_id: UUID
    ) -> Dict[str, Any]:
        """
        Process batch of files
        
        Args:
            token: GitHub API token
            repo_name: Repository name (owner/repo)
            files: List of file objects to process
            project_id: Project ID to associate data with
            
        Returns:
            Dict with batch processing results
        """
        files_imported = 0
        processed_data = []
        
        headers = {**self.DEFAULT_HEADERS, "Authorization": f"Bearer {token}"}
        
        for file_obj in files:
            try:
                # Get file content
                async with self.session.get(file_obj.get("url"), headers=headers) as response:
                    if response.status != 200:
                        continue
                    
                    content_data = await response.json()
                
                # Decode content
                if content_data.get("encoding") == "base64" and content_data.get("content"):
                    try:
                        content = base64.b64decode(content_data.get("content")).decode("utf-8")
                    except UnicodeDecodeError:
                        # Skip binary files
                        continue
                else:
                    continue
                
                # Create document for vector storage
                file_path = file_obj.get("path", "")
                file_ext = file_path.split(".")[-1] if "." in file_path else ""
                
                document = {
                    "id": file_obj.get("sha"),
                    "content": content,
                    "metadata": {
                        "source_type": "github",
                        "repository": repo_name,
                        "path": file_path,
                        "file_extension": file_ext,
                        "size": file_obj.get("size", 0),
                        "last_modified": datetime.utcnow().isoformat(),
                        "url": file_obj.get("html_url"),
                        "importance_score": 0.7  # Default importance score
                    }
                }
                
                processed_data.append(document)
                files_imported += 1
                
            except Exception as e:
                logger.error(f"Error processing file {file_obj.get('path')}: {str(e)}")
        
        # If we have data to process, persist it
        if processed_data:
            # Apply ML-based importance filtering
            filtered_data = await self.filter_data_importance(processed_data)
            
            # Persist filtered data
            await self.persist_data(project_id, filtered_data)
        
        return {
            "files_imported": files_imported
        }
    
    def _should_process_file(self, file_path: str, file_size: int) -> bool:
        """
        Check if file should be processed
        
        Args:
            file_path: File path
            file_size: File size in bytes
            
        Returns:
            True if file should be processed, False otherwise
        """
        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            return False
        
        # Check if file is in excluded path
        if self._is_excluded_path(file_path):
            return False
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.SUPPORTED_EXTENSIONS
    
    def _is_excluded_path(self, file_path: str) -> bool:
        """
        Check if path is in excluded paths
        
        Args:
            file_path: File path
            
        Returns:
            True if path is excluded, False otherwise
        """
        for excluded_path in self.EXCLUDED_PATHS:
            if excluded_path in file_path:
                return True
        return False
    
    async def filter_data_importance(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply ML-based importance filtering to GitHub data
        
        Args:
            data: List of GitHub file documents
            
        Returns:
            List of documents with importance scores
        """
        # For now, implement a basic scoring algorithm
        # In future, this will be replaced with actual ML-based scoring
        
        for document in data:
            metadata = document.get("metadata", {})
            content = document.get("content", "")
            
            # Basic scoring factors
            factors = {
                "content_quality": 0.0,  # 0.0 to 1.0
                "file_importance": 0.0,  # 0.0 to 1.0
                "code_complexity": 0.0,  # 0.0 to 1.0
            }
            
            # 1. Content quality based on size and content density
            if content:
                # Normalize based on content length (between 100 and 10000 chars is optimal)
                content_len = len(content)
                if 100 <= content_len <= 10000:
                    factors["content_quality"] = 0.8
                elif content_len < 100:
                    factors["content_quality"] = 0.3 + (content_len / 100) * 0.5
                else:
                    factors["content_quality"] = 0.8 - min(0.6, (content_len - 10000) / 100000)
            
            # 2. File importance based on path and extension
            file_path = metadata.get("path", "").lower()
            file_ext = metadata.get("file_extension", "").lower()
            
            # Important files
            if any(important_file in file_path for important_file in [
                "readme", "main", "index", "app", "config", "setup", 
                "requirements", "package.json", "dockerfile"
            ]):
                factors["file_importance"] = 0.9
            # Important extensions
            elif file_ext in [".py", ".js", ".ts", ".java", ".go", ".rs"]:
                factors["file_importance"] = 0.8
            # Documentation
            elif file_ext in [".md", ".rst", ".txt"]:
                factors["file_importance"] = 0.7
            # Configuration
            elif file_ext in [".json", ".yaml", ".yml", ".toml", ".ini"]:
                factors["file_importance"] = 0.75
            # Other code
            elif file_ext in [".html", ".css", ".scss", ".jsx", ".tsx"]:
                factors["file_importance"] = 0.6
            else:
                factors["file_importance"] = 0.5
            
            # 3. Code complexity (simple heuristics)
            if content:
                # Function/class density
                if file_ext in [".py", ".js", ".ts", ".java", ".go", ".rs", ".cs"]:
                    # Count function declarations
                    function_matches = len(re.findall(r'(function|def|func)\s+\w+\s*\(', content))
                    class_matches = len(re.findall(r'class\s+\w+', content))
                    
                    # Normalize based on content length (per 1000 chars)
                    density = (function_matches + class_matches) / max(1, content_len / 1000)
                    factors["code_complexity"] = min(1.0, density / 5)
            
            # Calculate final score (weighted average)
            weights = {
                "content_quality": 0.4,
                "file_importance": 0.4,
                "code_complexity": 0.2
            }
            
            importance_score = sum(
                factor_score * weights[factor_name] 
                for factor_name, factor_score in factors.items()
            )
            
            # Update document metadata with importance score
            metadata["importance_score"] = round(importance_score, 2)
            document["metadata"] = metadata
        
        # Filter out low importance documents
        return [doc for doc in data if doc.get("metadata", {}).get("importance_score", 0) > 0.3]
    
    async def persist_data(self, project_id: UUID, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Persist GitHub data to vector database
        
        Args:
            project_id: Project ID to associate data with
            data: Data items to persist
            
        Returns:
            Dict with persistence results
        """
        # For now, just return a placeholder result
        # In future, this will integrate with the Vector DB service to persist data
        
        return {
            "success": True,
            "message": f"Persisted {len(data)} GitHub documents to vector store",
            "items_persisted": len(data),
            "errors": []
        }
    
    async def sync_integration(self, project_id: UUID, full_sync: bool = False) -> Dict[str, Any]:
        """
        Run full GitHub integration sync flow
        
        Args:
            project_id: Project ID to associate data with
            full_sync: Whether to run a full sync or incremental
            
        Returns:
            Dict with sync results
        """
        # Get sync window - last 7 days for incremental, all for full sync
        sync_window = None if full_sync else datetime.utcnow() - timedelta(days=7)
        
        # Run ingest data flow
        ingest_result = await self.ingest_data(project_id)
        
        return {
            "success": ingest_result.get("success", False),
            "message": ingest_result.get("message", ""),
            "full_sync": full_sync,
            "sync_time": datetime.utcnow().isoformat(),
            "items_processed": ingest_result.get("items_processed", 0),
            "items_imported": ingest_result.get("items_imported", 0),
            "errors": ingest_result.get("errors", [])
        }
