"""
Production Jira Integration System for NeuroSync AI Backend
Handles Jira API connections, ticket ingestion, comments, and status tracking.
"""

import asyncio
import logging
import aiohttp
import base64
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from pydantic import BaseModel

class JiraIssueType(str, Enum):
    """Jira issue types."""
    STORY = "Story"
    TASK = "Task"
    BUG = "Bug"
    EPIC = "Epic"
    SUB_TASK = "Sub-task"
    IMPROVEMENT = "Improvement"
    NEW_FEATURE = "New Feature"

class JiraUser(BaseModel):
    """Jira user information."""
    account_id: str
    display_name: str
    email_address: Optional[str]
    active: bool = True

class JiraProject(BaseModel):
    """Jira project information."""
    id: str
    key: str
    name: str
    description: Optional[str]
    project_type_key: str
    url: str

class JiraIssue(BaseModel):
    """Jira issue information."""
    id: str
    key: str
    summary: str
    description: Optional[str]
    issue_type: str
    status: str
    priority: str
    resolution: Optional[str]
    assignee: Optional[JiraUser]
    reporter: JiraUser
    creator: JiraUser
    project: JiraProject
    labels: List[str] = []
    components: List[str] = []
    created: datetime
    updated: datetime
    resolved: Optional[datetime]
    story_points: Optional[int]
    parent_key: Optional[str]
    epic_key: Optional[str]
    url: str

class JiraComment(BaseModel):
    """Jira comment information."""
    id: str
    author: JiraUser
    body: str
    created: datetime
    updated: datetime
    issue_key: str

class JiraIntegrationConfig(BaseModel):
    """Jira integration configuration."""
    base_url: str  # e.g., https://company.atlassian.net
    username: str  # Email for cloud, username for server
    api_token: str  # API token for cloud, password for server
    is_cloud: bool = True
    max_results_per_page: int = 100
    include_archived: bool = False

class JiraIntegrationSystem:
    """
    Production-ready Jira integration system.
    Handles ticket ingestion, comment tracking, and project analysis.
    """
    
    def __init__(
        self,
        config: JiraIntegrationConfig,
        file_processor=None,
        vector_service=None,
        knowledge_graph_service=None,
        importance_filter=None
    ):
        """Initialize the Jira Integration System."""
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
        
        # API endpoints
        self.api_base = f"{self.config.base_url}/rest/api/3" if self.config.is_cloud else f"{self.config.base_url}/rest/api/2"
        
        self.logger.info("Jira Integration System initialized")
    
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
            # Create basic auth header
            auth_string = f"{self.config.username}:{self.config.api_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_header = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_header}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'NeuroSync-AI/1.0'
            }
            self._session = aiohttp.ClientSession(headers=headers)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Jira API connection and get server info."""
        await self._ensure_session()
        
        try:
            async with self._session.get(f"{self.api_base}/serverInfo") as response:
                if response.status == 200:
                    server_info = await response.json()
                    user_info = await self._get_current_user()
                    
                    return {
                        'status': 'connected',
                        'server': {
                            'version': server_info.get('version'),
                            'build_number': server_info.get('buildNumber'),
                            'server_title': server_info.get('serverTitle'),
                            'base_url': server_info.get('baseUrl')
                        },
                        'user': user_info,
                        'is_cloud': self.config.is_cloud
                    }
                else:
                    error_text = await response.text()
                    return {
                        'status': 'error',
                        'error': f'HTTP {response.status}: {error_text}',
                        'status_code': response.status
                    }
                    
        except Exception as e:
            self.logger.error(f"Jira connection test failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_projects(self, include_archived: bool = None) -> List[JiraProject]:
        """Get list of Jira projects."""
        await self._ensure_session()
        projects = []
        
        try:
            params = {'expand': 'description,lead,url,projectKeys'}
            
            if include_archived is not None:
                params['includeArchived'] = str(include_archived).lower()
            elif not self.config.include_archived:
                params['includeArchived'] = 'false'
            
            async with self._session.get(f"{self.api_base}/project", params=params) as response:
                if response.status == 200:
                    projects_data = await response.json()
                    
                    for project_data in projects_data:
                        project = JiraProject(
                            id=project_data['id'],
                            key=project_data['key'],
                            name=project_data['name'],
                            description=project_data.get('description'),
                            project_type_key=project_data.get('projectTypeKey', 'software'),
                            url=project_data.get('self', '')
                        )
                        projects.append(project)
                        
        except Exception as e:
            self.logger.error(f"Error fetching Jira projects: {str(e)}")
        
        self.logger.info(f"Retrieved {len(projects)} Jira projects")
        return projects
    
    async def get_project_issues(
        self,
        project_key: str,
        project_id: str,
        max_results: int = 1000,
        updated_since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get issues from a Jira project."""
        start_time = datetime.now()
        
        try:
            # Build JQL query
            jql_parts = [f"project = {project_key}"]
            
            if updated_since:
                jql_parts.append(f"updated >= '{updated_since.strftime('%Y-%m-%d %H:%M')}'")
            
            jql_query = " AND ".join(jql_parts)
            
            # Get issues in batches
            all_issues = []
            start_at = 0
            
            while len(all_issues) < max_results:
                batch_size = min(self.config.max_results_per_page, max_results - len(all_issues))
                
                issues_batch = await self._search_issues(
                    jql_query=jql_query,
                    start_at=start_at,
                    max_results=batch_size
                )
                
                if not issues_batch:
                    break
                
                all_issues.extend(issues_batch)
                start_at += len(issues_batch)
                
                if len(issues_batch) < batch_size:
                    break
            
            # Process issues
            processed_issues = 0
            failed_issues = 0
            
            for issue in all_issues:
                try:
                    # Process issue content
                    await self._process_issue_content(issue, project_id)
                    
                    # Get and process comments
                    comments = await self._get_issue_comments(issue.key)
                    for comment in comments:
                        await self._process_comment_content(comment, project_id)
                    
                    # Create entities in knowledge graph
                    if self.knowledge_graph_service:
                        await self._create_issue_entities(issue, comments, project_id)
                    
                    processed_issues += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing issue {issue.key}: {str(e)}")
                    failed_issues += 1
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                'status': 'completed',
                'project_key': project_key,
                'total_issues': len(all_issues),
                'processed_issues': processed_issues,
                'failed_issues': failed_issues,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error getting project issues for {project_key}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'processing_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
    
    async def sync_project_data(
        self,
        jira_project_key: str,
        neurosync_project_id: str,
        full_sync: bool = False
    ) -> Dict[str, Any]:
        """Synchronize Jira project data with NeuroSync."""
        start_time = datetime.now()
        
        try:
            # Determine sync window
            updated_since = None
            if not full_sync:
                updated_since = datetime.now() - timedelta(days=7)
            
            # Get project issues
            issues_result = await self.get_project_issues(
                project_key=jira_project_key,
                project_id=neurosync_project_id,
                max_results=5000,
                updated_since=updated_since
            )
            
            # Create project entity in knowledge graph
            if self.knowledge_graph_service:
                project_info = await self._get_project_info(jira_project_key)
                if project_info:
                    await self._create_project_entities(project_info, neurosync_project_id)
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                'status': 'completed',
                'sync_type': 'full' if full_sync else 'incremental',
                'jira_project': jira_project_key,
                'neurosync_project': neurosync_project_id,
                'issues_processed': issues_result.get('processed_issues', 0),
                'issues_failed': issues_result.get('failed_issues', 0),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error syncing project {jira_project_key}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'processing_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
    
    async def _get_current_user(self) -> Dict[str, Any]:
        """Get current user information."""
        try:
            async with self._session.get(f"{self.api_base}/myself") as response:
                if response.status == 200:
                    user_data = await response.json()
                    return {
                        'account_id': user_data.get('accountId'),
                        'display_name': user_data.get('displayName'),
                        'email_address': user_data.get('emailAddress'),
                        'active': user_data.get('active', True)
                    }
        except Exception as e:
            self.logger.error(f"Error getting current user: {str(e)}")
        
        return {}
    
    async def _search_issues(
        self,
        jql_query: str,
        start_at: int = 0,
        max_results: int = 100
    ) -> List[JiraIssue]:
        """Search for issues using JQL."""
        await self._ensure_session()
        issues = []
        
        try:
            payload = {
                'jql': jql_query,
                'startAt': start_at,
                'maxResults': max_results,
                'expand': ['names', 'schema'],
                'fields': ['*all']
            }
            
            async with self._session.post(f"{self.api_base}/search", json=payload) as response:
                if response.status == 200:
                    search_result = await response.json()
                    
                    for issue_data in search_result.get('issues', []):
                        issue = self._parse_issue(issue_data)
                        if issue:
                            issues.append(issue)
                            
        except Exception as e:
            self.logger.error(f"Error searching issues: {str(e)}")
        
        return issues
    
    async def _get_issue_comments(self, issue_key: str) -> List[JiraComment]:
        """Get comments for an issue."""
        await self._ensure_session()
        comments = []
        
        try:
            async with self._session.get(f"{self.api_base}/issue/{issue_key}/comment") as response:
                if response.status == 200:
                    comments_data = await response.json()
                    
                    for comment_data in comments_data.get('comments', []):
                        comment = JiraComment(
                            id=comment_data['id'],
                            author=self._parse_user(comment_data['author']),
                            body=comment_data['body'],
                            created=datetime.fromisoformat(comment_data['created'].replace('Z', '+00:00')),
                            updated=datetime.fromisoformat(comment_data['updated'].replace('Z', '+00:00')),
                            issue_key=issue_key
                        )
                        comments.append(comment)
                        
        except Exception as e:
            self.logger.error(f"Error getting comments for issue {issue_key}: {str(e)}")
        
        return comments
    
    async def _get_project_info(self, project_key: str) -> Optional[JiraProject]:
        """Get detailed project information."""
        await self._ensure_session()
        
        try:
            params = {'expand': 'description,lead,url,projectKeys'}
            
            async with self._session.get(f"{self.api_base}/project/{project_key}", params=params) as response:
                if response.status == 200:
                    project_data = await response.json()
                    
                    return JiraProject(
                        id=project_data['id'],
                        key=project_data['key'],
                        name=project_data['name'],
                        description=project_data.get('description'),
                        project_type_key=project_data.get('projectTypeKey', 'software'),
                        url=project_data.get('self', '')
                    )
                    
        except Exception as e:
            self.logger.error(f"Error getting project info for {project_key}: {str(e)}")
        
        return None
    
    def _parse_issue(self, issue_data: Dict[str, Any]) -> Optional[JiraIssue]:
        """Parse issue data from Jira API response."""
        try:
            fields = issue_data['fields']
            
            # Parse dates
            created = datetime.fromisoformat(fields['created'].replace('Z', '+00:00'))
            updated = datetime.fromisoformat(fields['updated'].replace('Z', '+00:00'))
            resolved = None
            if fields.get('resolutiondate'):
                resolved = datetime.fromisoformat(fields['resolutiondate'].replace('Z', '+00:00'))
            
            # Parse project
            project_data = fields['project']
            project = JiraProject(
                id=project_data['id'],
                key=project_data['key'],
                name=project_data['name'],
                description=project_data.get('description'),
                project_type_key=project_data.get('projectTypeKey', 'software'),
                url=project_data.get('self', '')
            )
            
            # Extract custom fields
            story_points = None
            if 'customfield_10016' in fields and fields['customfield_10016']:
                story_points = int(fields['customfield_10016'])
            
            epic_key = None
            if 'customfield_10014' in fields and fields['customfield_10014']:
                epic_key = fields['customfield_10014']
            
            return JiraIssue(
                id=issue_data['id'],
                key=issue_data['key'],
                summary=fields['summary'],
                description=fields.get('description', ''),
                issue_type=fields['issuetype']['name'],
                status=fields['status']['name'],
                priority=fields['priority']['name'] if fields.get('priority') else 'Medium',
                resolution=fields['resolution']['name'] if fields.get('resolution') else None,
                assignee=self._parse_user(fields.get('assignee')) if fields.get('assignee') else None,
                reporter=self._parse_user(fields['reporter']),
                creator=self._parse_user(fields['creator']),
                project=project,
                labels=fields.get('labels', []),
                components=[comp['name'] for comp in fields.get('components', [])],
                created=created,
                updated=updated,
                resolved=resolved,
                story_points=story_points,
                parent_key=fields['parent']['key'] if fields.get('parent') else None,
                epic_key=epic_key,
                url=f"{self.config.base_url}/browse/{issue_data['key']}"
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing issue data: {str(e)}")
            return None
    
    def _parse_user(self, user_data: Dict[str, Any]) -> JiraUser:
        """Parse user data from Jira API response."""
        return JiraUser(
            account_id=user_data.get('accountId', user_data.get('name', '')),
            display_name=user_data.get('displayName', ''),
            email_address=user_data.get('emailAddress'),
            active=user_data.get('active', True)
        )
    
    async def _process_issue_content(self, issue: JiraIssue, project_id: str) -> None:
        """Process issue content for vector storage."""
        if not self.file_processor:
            return
        
        try:
            content_parts = [
                f"Issue: {issue.key}",
                f"Summary: {issue.summary}",
                f"Type: {issue.issue_type}",
                f"Status: {issue.status}",
                f"Priority: {issue.priority}"
            ]
            
            if issue.description:
                content_parts.append(f"Description: {issue.description}")
            
            if issue.labels:
                content_parts.append(f"Labels: {', '.join(issue.labels)}")
            
            if issue.components:
                content_parts.append(f"Components: {', '.join(issue.components)}")
            
            content = "\n\n".join(content_parts)
            
            await self.file_processor.upload_file(
                file_content=content.encode('utf-8'),
                filename=f"{issue.key}.txt",
                project_id=project_id,
                user_id='jira_integration',
                source='jira'
            )
            
        except Exception as e:
            self.logger.error(f"Error processing issue content for {issue.key}: {str(e)}")
    
    async def _process_comment_content(self, comment: JiraComment, project_id: str) -> None:
        """Process comment content for vector storage."""
        if not self.file_processor or not comment.body.strip():
            return
        
        try:
            content = f"Comment on {comment.issue_key} by {comment.author.display_name}:\n\n{comment.body}"
            
            await self.file_processor.upload_file(
                file_content=content.encode('utf-8'),
                filename=f"{comment.issue_key}_comment_{comment.id}.txt",
                project_id=project_id,
                user_id='jira_integration',
                source='jira'
            )
            
        except Exception as e:
            self.logger.error(f"Error processing comment content for {comment.id}: {str(e)}")
    
    async def _create_issue_entities(
        self,
        issue: JiraIssue,
        comments: List[JiraComment],
        project_id: str
    ) -> None:
        """Create issue entities in knowledge graph."""
        if not self.knowledge_graph_service:
            return
        
        try:
            # Create issue entity
            await self.knowledge_graph_service.add_entity(
                project_id=project_id,
                entity_type='Issue',
                entity_id=issue.key,
                properties={
                    'summary': issue.summary,
                    'description': issue.description or '',
                    'issue_type': issue.issue_type,
                    'status': issue.status,
                    'priority': issue.priority,
                    'labels': issue.labels,
                    'components': issue.components,
                    'story_points': issue.story_points,
                    'created': issue.created.isoformat(),
                    'updated': issue.updated.isoformat(),
                    'url': issue.url
                }
            )
            
            # Create user entities and relationships
            for user_field, relationship in [
                (issue.reporter, 'REPORTED'),
                (issue.assignee, 'ASSIGNED_TO'),
                (issue.creator, 'CREATED')
            ]:
                if user_field:
                    await self.knowledge_graph_service.add_entity(
                        project_id=project_id,
                        entity_type='Person',
                        entity_id=user_field.account_id,
                        properties={
                            'display_name': user_field.display_name,
                            'email': user_field.email_address,
                            'platform': 'jira'
                        }
                    )
                    
                    await self.knowledge_graph_service.add_relationship(
                        project_id=project_id,
                        from_entity_type='Person',
                        from_entity_id=user_field.account_id,
                        to_entity_type='Issue',
                        to_entity_id=issue.key,
                        relationship_type=relationship,
                        properties={
                            'platform': 'jira',
                            'created_at': issue.created.isoformat()
                        }
                    )
            
        except Exception as e:
            self.logger.error(f"Error creating issue entities: {str(e)}")
    
    async def _create_project_entities(
        self,
        project: JiraProject,
        neurosync_project_id: str
    ) -> None:
        """Create project entities in knowledge graph."""
        if not self.knowledge_graph_service:
            return
        
        try:
            await self.knowledge_graph_service.add_entity(
                project_id=neurosync_project_id,
                entity_type='JiraProject',
                entity_id=project.key,
                properties={
                    'name': project.name,
                    'description': project.description or '',
                    'project_type': project.project_type_key,
                    'url': project.url,
                    'platform': 'jira'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creating project entities: {str(e)}")
