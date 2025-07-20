"""
Production GitHub Integration System for NeuroSync AI Backend
Handles GitHub API connections, repository scanning, webhooks, and code processing.
"""

import os
import asyncio
import logging
import aiohttp
import base64
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from pathlib import Path

from pydantic import BaseModel

class GitHubEventType(str, Enum):
    """GitHub webhook event types."""
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    ISSUES = "issues"
    COMMIT_COMMENT = "commit_comment"
    PULL_REQUEST_REVIEW = "pull_request_review"
    RELEASE = "release"

class RepositoryInfo(BaseModel):
    """GitHub repository information."""
    id: int
    name: str
    full_name: str
    owner: str
    description: Optional[str]
    private: bool
    default_branch: str
    language: Optional[str]
    languages: Dict[str, int] = {}
    size: int
    stargazers_count: int
    forks_count: int
    created_at: datetime
    updated_at: datetime
    html_url: str

class FileInfo(BaseModel):
    """GitHub file information."""
    path: str
    name: str
    sha: str
    size: int
    type: str
    download_url: Optional[str]

class CommitInfo(BaseModel):
    """GitHub commit information."""
    sha: str
    author: Dict[str, Any]
    message: str
    timestamp: datetime
    url: str
    added_files: List[str] = []
    modified_files: List[str] = []
    removed_files: List[str] = []

class GitHubIntegrationConfig(BaseModel):
    """GitHub integration configuration."""
    access_token: str
    webhook_secret: Optional[str] = None
    api_base_url: str = "https://api.github.com"
    max_file_size: int = 1024 * 1024  # 1MB
    supported_extensions: Set[str] = {
        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.php',
        '.rb', '.go', '.rs', '.kt', '.swift', '.scala', '.r', '.sql',
        '.html', '.css', '.scss', '.less', '.vue', '.jsx', '.tsx',
        '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg',
        '.md', '.txt', '.rst', '.adoc'
    }
    excluded_paths: Set[str] = {
        'node_modules', '.git', '.vscode', '.idea', '__pycache__',
        'venv', 'env', 'dist', 'build', 'target', '.next', '.nuxt'
    }

class GitHubIntegrationSystem:
    """
    Production-ready GitHub integration system.
    Handles repository scanning, webhook processing, and code analysis.
    """
    
    def __init__(
        self,
        config: GitHubIntegrationConfig,
        file_processor=None,
        vector_service=None,
        knowledge_graph_service=None,
        importance_filter=None
    ):
        """Initialize the GitHub Integration System."""
        self.config = config
        self.file_processor = file_processor
        self.vector_service = vector_service
        self.knowledge_graph_service = knowledge_graph_service
        self.importance_filter = importance_filter
        
        # HTTP session for API calls
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Thread pool for CPU-intensive operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self._rate_limit_remaining = 5000
        self._rate_limit_reset = datetime.now()
        
        self.logger.info("GitHub Integration System initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def _ensure_session(self):
        """Ensure HTTP session is available."""
        if not self._session or self._session.closed:
            headers = {
                'Authorization': f'token {self.config.access_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'NeuroSync-AI/1.0'
            }
            self._session = aiohttp.ClientSession(headers=headers)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test GitHub API connection and get user info."""
        await self._ensure_session()
        
        try:
            async with self._session.get(f"{self.config.api_base_url}/user") as response:
                if response.status == 200:
                    user_data = await response.json()
                    self._update_rate_limit(response.headers)
                    
                    return {
                        'status': 'connected',
                        'user': {
                            'login': user_data.get('login'),
                            'name': user_data.get('name'),
                            'email': user_data.get('email'),
                            'public_repos': user_data.get('public_repos'),
                            'private_repos': user_data.get('total_private_repos')
                        },
                        'rate_limit': {
                            'remaining': self._rate_limit_remaining,
                            'reset_at': self._rate_limit_reset.isoformat()
                        }
                    }
                else:
                    error_data = await response.json()
                    return {
                        'status': 'error',
                        'error': error_data.get('message', 'Unknown error'),
                        'status_code': response.status
                    }
                    
        except Exception as e:
            self.logger.error(f"GitHub connection test failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_user_repositories(
        self,
        include_private: bool = True,
        include_forks: bool = False
    ) -> List[RepositoryInfo]:
        """Get list of user's repositories."""
        await self._ensure_session()
        repositories = []
        page = 1
        per_page = 100
        
        while True:
            try:
                params = {
                    'type': 'all' if include_private else 'public',
                    'sort': 'updated',
                    'direction': 'desc',
                    'per_page': per_page,
                    'page': page
                }
                
                async with self._session.get(f"{self.config.api_base_url}/user/repos", params=params) as response:
                    if response.status != 200:
                        break
                    
                    repos_data = await response.json()
                    self._update_rate_limit(response.headers)
                    
                    if not repos_data:
                        break
                    
                    for repo_data in repos_data:
                        # Skip forks if not requested
                        if not include_forks and repo_data.get('fork', False):
                            continue
                        
                        repo_info = RepositoryInfo(
                            id=repo_data['id'],
                            name=repo_data['name'],
                            full_name=repo_data['full_name'],
                            owner=repo_data['owner']['login'],
                            description=repo_data.get('description'),
                            private=repo_data['private'],
                            default_branch=repo_data['default_branch'],
                            language=repo_data.get('language'),
                            size=repo_data['size'],
                            stargazers_count=repo_data['stargazers_count'],
                            forks_count=repo_data['forks_count'],
                            created_at=datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00')),
                            updated_at=datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00')),
                            html_url=repo_data['html_url']
                        )
                        
                        # Get repository languages
                        repo_info.languages = await self._get_repository_languages(repo_data['full_name'])
                        
                        repositories.append(repo_info)
                    
                    page += 1
                    
                    # Break if we got less than per_page results (last page)
                    if len(repos_data) < per_page:
                        break
                        
            except Exception as e:
                self.logger.error(f"Error fetching repositories: {str(e)}")
                break
        
        self.logger.info(f"Retrieved {len(repositories)} repositories")
        return repositories
    
    async def scan_repository(
        self,
        repo_full_name: str,
        project_id: str,
        branch: str = None,
        max_files: int = 1000
    ) -> Dict[str, Any]:
        """Scan a repository and process its files."""
        start_time = datetime.now()
        
        try:
            # Get repository info
            repo_info = await self._get_repository_info(repo_full_name)
            if not repo_info:
                return {
                    'status': 'error',
                    'error': 'Repository not found or not accessible'
                }
            
            scan_branch = branch or repo_info.default_branch
            
            # Get repository tree
            files = await self._get_repository_tree(repo_full_name, scan_branch)
            
            # Filter files by extension and size
            processable_files = []
            for file_info in files:
                if self._should_process_file(file_info):
                    processable_files.append(file_info)
                    if len(processable_files) >= max_files:
                        break
            
            # Process files in batches
            processed_files = 0
            failed_files = 0
            batch_size = 10
            
            for i in range(0, len(processable_files), batch_size):
                batch = processable_files[i:i + batch_size]
                batch_results = await self._process_file_batch(batch, repo_full_name, project_id, scan_branch)
                
                for result in batch_results:
                    if result.get('status') == 'success':
                        processed_files += 1
                    else:
                        failed_files += 1
            
            # Create repository entity in knowledge graph
            if self.knowledge_graph_service:
                await self._create_repository_entities(repo_info, project_id)
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                'status': 'completed',
                'repository': repo_info.dict(),
                'branch': scan_branch,
                'total_files': len(files),
                'processable_files': len(processable_files),
                'processed_files': processed_files,
                'failed_files': failed_files,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error scanning repository {repo_full_name}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'processing_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
    
    async def get_recent_commits(
        self,
        repo_full_name: str,
        branch: str = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CommitInfo]:
        """Get recent commits from a repository."""
        await self._ensure_session()
        commits = []
        
        try:
            params = {
                'per_page': min(limit, 100),
                'page': 1
            }
            
            if branch:
                params['sha'] = branch
            
            if since:
                params['since'] = since.isoformat()
            
            async with self._session.get(f"{self.config.api_base_url}/repos/{repo_full_name}/commits", params=params) as response:
                if response.status == 200:
                    commits_data = await response.json()
                    self._update_rate_limit(response.headers)
                    
                    for commit_data in commits_data:
                        commit_info = CommitInfo(
                            sha=commit_data['sha'],
                            author=commit_data['commit']['author'],
                            message=commit_data['commit']['message'],
                            timestamp=datetime.fromisoformat(commit_data['commit']['author']['date'].replace('Z', '+00:00')),
                            url=commit_data['html_url']
                        )
                        
                        # Get file changes for this commit
                        file_changes = await self._get_commit_file_changes(repo_full_name, commit_data['sha'])
                        commit_info.added_files = file_changes.get('added', [])
                        commit_info.modified_files = file_changes.get('modified', [])
                        commit_info.removed_files = file_changes.get('removed', [])
                        
                        commits.append(commit_info)
                        
                        if len(commits) >= limit:
                            break
                            
        except Exception as e:
            self.logger.error(f"Error fetching commits for {repo_full_name}: {str(e)}")
        
        return commits
    
    async def process_webhook_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        project_id: str
    ) -> Dict[str, Any]:
        """Process a GitHub webhook event."""
        try:
            if event_type == GitHubEventType.PUSH:
                return await self._process_push_event(payload, project_id)
            elif event_type == GitHubEventType.PULL_REQUEST:
                return await self._process_pull_request_event(payload, project_id)
            elif event_type == GitHubEventType.ISSUES:
                return await self._process_issues_event(payload, project_id)
            else:
                return {
                    'status': 'skipped',
                    'message': f'Event type {event_type} not handled'
                }
                
        except Exception as e:
            self.logger.error(f"Error processing webhook event {event_type}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _update_rate_limit(self, headers):
        """Update rate limit information from response headers."""
        try:
            self._rate_limit_remaining = int(headers.get('X-RateLimit-Remaining', 5000))
            reset_timestamp = int(headers.get('X-RateLimit-Reset', 0))
            if reset_timestamp:
                self._rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
        except (ValueError, TypeError):
            pass
    
    async def _get_repository_info(self, repo_full_name: str) -> Optional[RepositoryInfo]:
        """Get detailed repository information."""
        await self._ensure_session()
        
        try:
            async with self._session.get(f"{self.config.api_base_url}/repos/{repo_full_name}") as response:
                if response.status == 200:
                    repo_data = await response.json()
                    self._update_rate_limit(response.headers)
                    
                    return RepositoryInfo(
                        id=repo_data['id'],
                        name=repo_data['name'],
                        full_name=repo_data['full_name'],
                        owner=repo_data['owner']['login'],
                        description=repo_data.get('description'),
                        private=repo_data['private'],
                        default_branch=repo_data['default_branch'],
                        language=repo_data.get('language'),
                        size=repo_data['size'],
                        stargazers_count=repo_data['stargazers_count'],
                        forks_count=repo_data['forks_count'],
                        created_at=datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00')),
                        html_url=repo_data['html_url']
                    )
        except Exception as e:
            self.logger.error(f"Error getting repository info for {repo_full_name}: {str(e)}")
        
        return None
    
    async def _get_repository_languages(self, repo_full_name: str) -> Dict[str, int]:
        """Get repository programming languages."""
        await self._ensure_session()
        
        try:
            async with self._session.get(f"{self.config.api_base_url}/repos/{repo_full_name}/languages") as response:
                if response.status == 200:
                    languages = await response.json()
                    self._update_rate_limit(response.headers)
                    return languages
        except Exception as e:
            self.logger.error(f"Error getting languages for {repo_full_name}: {str(e)}")
        
        return {}
    
    async def _get_repository_tree(
        self,
        repo_full_name: str,
        branch: str,
        recursive: bool = True
    ) -> List[FileInfo]:
        """Get repository file tree."""
        await self._ensure_session()
        files = []
        
        try:
            params = {'recursive': '1'} if recursive else {}
            
            async with self._session.get(f"{self.config.api_base_url}/repos/{repo_full_name}/git/trees/{branch}", params=params) as response:
                if response.status == 200:
                    tree_data = await response.json()
                    self._update_rate_limit(response.headers)
                    
                    for item in tree_data.get('tree', []):
                        if item['type'] == 'blob':  # Only files, not directories
                            file_info = FileInfo(
                                path=item['path'],
                                name=Path(item['path']).name,
                                sha=item['sha'],
                                size=item.get('size', 0),
                                type=item['type'],
                                download_url=f"https://raw.githubusercontent.com/{repo_full_name}/{branch}/{item['path']}"
                            )
                            files.append(file_info)
                            
        except Exception as e:
            self.logger.error(f"Error getting repository tree for {repo_full_name}: {str(e)}")
        
        return files
    
    def _should_process_file(self, file_info: FileInfo) -> bool:
        """Determine if a file should be processed."""
        # Check file size
        if file_info.size > self.config.max_file_size:
            return False
        
        # Check file extension
        file_path = Path(file_info.path)
        if file_path.suffix.lower() not in self.config.supported_extensions:
            return False
        
        # Check excluded paths
        path_parts = set(file_path.parts)
        if path_parts.intersection(self.config.excluded_paths):
            return False
        
        return True
    
    async def _process_file_batch(
        self,
        files: List[FileInfo],
        repo_full_name: str,
        project_id: str,
        branch: str
    ) -> List[Dict[str, Any]]:
        """Process a batch of files."""
        results = []
        
        # Download file contents
        for file_info in files:
            try:
                content = await self._download_file_content(repo_full_name, file_info.path, branch)
                if content and self.file_processor:
                    # Process file through the file processing system
                    result = await self.file_processor.upload_file(
                        file_content=content.encode('utf-8'),
                        filename=file_info.name,
                        project_id=project_id,
                        user_id='github_integration',
                        source='github'
                    )
                    results.append({
                        'file_path': file_info.path,
                        'status': 'success' if result.status.value == 'completed' else 'failed',
                        'file_id': result.file_id,
                        'message': result.message
                    })
                else:
                    results.append({
                        'file_path': file_info.path,
                        'status': 'skipped',
                        'message': 'No content or file processor not available'
                    })
                    
            except Exception as e:
                results.append({
                    'file_path': file_info.path,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results
    
    async def _download_file_content(
        self,
        repo_full_name: str,
        file_path: str,
        branch: str
    ) -> Optional[str]:
        """Download file content from GitHub."""
        await self._ensure_session()
        
        try:
            async with self._session.get(f"{self.config.api_base_url}/repos/{repo_full_name}/contents/{file_path}", params={'ref': branch}) as response:
                if response.status == 200:
                    file_data = await response.json()
                    self._update_rate_limit(response.headers)
                    
                    if file_data.get('encoding') == 'base64':
                        content = base64.b64decode(file_data['content']).decode('utf-8')
                        return content
                        
        except Exception as e:
            self.logger.error(f"Error downloading file {file_path}: {str(e)}")
        
        return None
    
    async def _get_commit_file_changes(
        self,
        repo_full_name: str,
        commit_sha: str
    ) -> Dict[str, List[str]]:
        """Get file changes for a specific commit."""
        await self._ensure_session()
        changes = {'added': [], 'modified': [], 'removed': []}
        
        try:
            async with self._session.get(f"{self.config.api_base_url}/repos/{repo_full_name}/commits/{commit_sha}") as response:
                if response.status == 200:
                    commit_data = await response.json()
                    self._update_rate_limit(response.headers)
                    
                    for file_change in commit_data.get('files', []):
                        filename = file_change['filename']
                        status = file_change['status']
                        
                        if status == 'added':
                            changes['added'].append(filename)
                        elif status == 'modified':
                            changes['modified'].append(filename)
                        elif status == 'removed':
                            changes['removed'].append(filename)
                            
        except Exception as e:
            self.logger.error(f"Error getting commit changes for {commit_sha}: {str(e)}")
        
        return changes
    
    async def _create_repository_entities(
        self,
        repo_info: RepositoryInfo,
        project_id: str
    ) -> None:
        """Create repository entities in knowledge graph."""
        if not self.knowledge_graph_service:
            return
        
        try:
            # Create repository entity
            await self.knowledge_graph_service.add_entity(
                project_id=project_id,
                entity_type='Repository',
                entity_id=repo_info.full_name,
                properties={
                    'name': repo_info.name,
                    'description': repo_info.description,
                    'language': repo_info.language,
                    'languages': repo_info.languages,
                    'private': repo_info.private,
                    'stars': repo_info.stargazers_count,
                    'forks': repo_info.forks_count,
                    'size': repo_info.size,
                    'created_at': repo_info.created_at.isoformat(),
                    'updated_at': repo_info.updated_at.isoformat(),
                    'url': repo_info.html_url
                }
            )
            
            # Create owner entity
            await self.knowledge_graph_service.add_entity(
                project_id=project_id,
                entity_type='Person',
                entity_id=repo_info.owner,
                properties={
                    'username': repo_info.owner,
                    'platform': 'github'
                }
            )
            
            # Create relationship
            await self.knowledge_graph_service.add_relationship(
                project_id=project_id,
                from_entity_type='Person',
                from_entity_id=repo_info.owner,
                to_entity_type='Repository',
                to_entity_id=repo_info.full_name,
                relationship_type='OWNS',
                properties={
                    'platform': 'github',
                    'created_at': repo_info.created_at.isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creating repository entities: {str(e)}")
    
    async def _process_push_event(
        self,
        payload: Dict[str, Any],
        project_id: str
    ) -> Dict[str, Any]:
        """Process GitHub push event."""
        repo_name = payload['repository']['full_name']
        commits = payload.get('commits', [])
        
        self.logger.info(f"Processing push event for {repo_name} with {len(commits)} commits")
        
        # Process each commit
        processed_commits = 0
        for commit_data in commits:
            try:
                # Process changed files
                changed_files = commit_data.get('added', []) + commit_data.get('modified', [])
                if changed_files and self.file_processor:
                    for file_path in changed_files:
                        if self._should_process_file(FileInfo(path=file_path, name=Path(file_path).name, sha='', size=0, type='blob')):
                            # Download and process the file
                            content = await self._download_file_content(repo_name, file_path, payload['after'])
                            if content:
                                await self.file_processor.upload_file(
                                    file_content=content.encode('utf-8'),
                                    filename=Path(file_path).name,
                                    project_id=project_id,
                                    user_id='github_integration',
                                    source='github'
                                )
                
                processed_commits += 1
                
            except Exception as e:
                self.logger.error(f"Error processing commit {commit_data.get('id', 'unknown')}: {str(e)}")
        
        return {
            'status': 'completed',
            'event_type': 'push',
            'repository': repo_name,
            'total_commits': len(commits),
            'processed_commits': processed_commits
        }
    
    async def _process_pull_request_event(
        self,
        payload: Dict[str, Any],
        project_id: str
    ) -> Dict[str, Any]:
        """Process GitHub pull request event."""
        action = payload['action']
        pr_data = payload['pull_request']
        
        self.logger.info(f"Processing pull request {action} event for PR #{pr_data['number']}")
        
        # Create PR entity in knowledge graph if opened
        if action == 'opened' and self.knowledge_graph_service:
            try:
                await self.knowledge_graph_service.add_entity(
                    project_id=project_id,
                    entity_type='PullRequest',
                    entity_id=f"pr_{pr_data['id']}",
                    properties={
                        'number': pr_data['number'],
                        'title': pr_data['title'],
                        'body': pr_data.get('body', ''),
                        'state': pr_data['state'],
                        'author': pr_data['user']['login'],
                        'created_at': pr_data['created_at'],
                        'url': pr_data['html_url']
                    }
                )
            except Exception as e:
                self.logger.error(f"Error creating PR entity: {str(e)}")
        
        return {
            'status': 'completed',
            'event_type': 'pull_request',
            'action': action,
            'pr_number': pr_data['number']
        }
    
    async def _process_issues_event(
        self,
        payload: Dict[str, Any],
        project_id: str
    ) -> Dict[str, Any]:
        """Process GitHub issues event."""
        action = payload['action']
        issue_data = payload['issue']
        
        self.logger.info(f"Processing issue {action} event for issue #{issue_data['number']}")
        
        # Create issue entity in knowledge graph if opened
        if action == 'opened' and self.knowledge_graph_service:
            try:
                await self.knowledge_graph_service.add_entity(
                    project_id=project_id,
                    entity_type='Issue',
                    entity_id=f"issue_{issue_data['id']}",
                    properties={
                        'number': issue_data['number'],
                        'title': issue_data['title'],
                        'body': issue_data.get('body', ''),
                        'state': issue_data['state'],
                        'author': issue_data['user']['login'],
                        'labels': [label['name'] for label in issue_data.get('labels', [])],
                        'created_at': issue_data['created_at'],
                        'url': issue_data['html_url']
                    }
                )
            except Exception as e:
                self.logger.error(f"Error creating issue entity: {str(e)}")
        
        return {
            'status': 'completed',
            'event_type': 'issues',
            'action': action,
            'issue_number': issue_data['number']
        }
