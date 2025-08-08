"""
Jira Integration Service for NeuroSync API
Handles Jira API authentication, project discovery, and issue ingestion
"""

import logging
import aiohttp
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session
from models.integration import Integration
from models.project import Project
from .base import BaseIntegrationService

# Create logger
logger = logging.getLogger(__name__)

class JiraIntegrationService(BaseIntegrationService):
    """
    Jira Integration Service
    Handles Jira API authentication, project discovery, and issue ingestion
    """
    
    # Default API paths
    CLOUD_API_BASE = "/rest/api/3"
    SERVER_API_BASE = "/rest/api/2"
    
    def __init__(self, db: Session, integration: Optional[Integration] = None):
        """
        Initialize Jira integration service
        
        Args:
            db: SQLAlchemy database session
            integration: Optional Integration model instance
        """
        super().__init__(db, integration)
        self.session = None
        self.api_base = self.CLOUD_API_BASE  # Default to cloud API
        
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
        Test Jira API connection
        
        Args:
            config: Jira integration config (url, username, token)
            
        Returns:
            Dict with connection test results
        """
        url = config.get("url")
        username = config.get("username")
        api_token = config.get("token")
        
        if not all([url, username, api_token]):
            return {
                "success": False,
                "message": "Jira URL, username, and API token are required"
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Normalize URL
            url = self._normalize_url(url)
            
            # Determine if cloud or server instance
            is_cloud = self._is_cloud_instance(url)
            self.api_base = self.CLOUD_API_BASE if is_cloud else self.SERVER_API_BASE
            
            # Test API connection by getting server info
            endpoint = f"{url}{self.api_base}/serverInfo"
            auth = aiohttp.BasicAuth(username, api_token)
            
            async with self.session.get(endpoint, auth=auth) as response:
                if response.status == 200:
                    server_info = await response.json()
                    return {
                        "success": True,
                        "message": f"Successfully connected to Jira {server_info.get('version')}",
                        "details": {
                            "server_title": server_info.get("serverTitle"),
                            "version": server_info.get("version"),
                            "base_url": server_info.get("baseUrl"),
                            "is_cloud": is_cloud
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "message": f"Jira API error: {error_text}",
                        "details": {"status_code": response.status}
                    }
        except Exception as e:
            logger.error(f"Error testing Jira connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to Jira: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def get_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get Jira metadata (projects, issue types, etc.)
        
        Args:
            config: Jira integration config (url, username, token)
            
        Returns:
            Dict with Jira metadata
        """
        url = config.get("url")
        username = config.get("username")
        api_token = config.get("token")
        
        if not all([url, username, api_token]):
            return {
                "success": False,
                "message": "Jira URL, username, and API token are required"
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Normalize URL
            url = self._normalize_url(url)
            
            # Determine if cloud or server instance
            is_cloud = self._is_cloud_instance(url)
            self.api_base = self.CLOUD_API_BASE if is_cloud else self.SERVER_API_BASE
            
            # Get projects
            endpoint = f"{url}{self.api_base}/project"
            auth = aiohttp.BasicAuth(username, api_token)
            
            async with self.session.get(endpoint, auth=auth) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "message": f"Jira API error: {error_text}",
                        "details": {"status_code": response.status}
                    }
                
                projects_data = await response.json()
            
            # Format project data
            projects = []
            for project in projects_data:
                projects.append({
                    "id": project.get("id"),
                    "key": project.get("key"),
                    "name": project.get("name"),
                    "url": f"{url}/projects/{project.get('key')}",
                    "avatar_url": project.get("avatarUrls", {}).get("48x48") if "avatarUrls" in project else None
                })
            
            # Get current user info
            endpoint = f"{url}{self.api_base}/myself"
            async with self.session.get(endpoint, auth=auth) as response:
                if response.status != 200:
                    user_data = {"error": "Could not retrieve user information"}
                else:
                    user_data = await response.json()
            
            return {
                "success": True,
                "user": {
                    "display_name": user_data.get("displayName"),
                    "email": user_data.get("emailAddress"),
                    "account_id": user_data.get("accountId"),
                    "active": user_data.get("active", True)
                },
                "projects": projects,
                "project_count": len(projects),
                "is_cloud": is_cloud
            }
        except Exception as e:
            logger.error(f"Error getting Jira metadata: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Jira metadata: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def ingest_data(self, config: Dict[str, Any], project_id: UUID) -> Dict[str, Any]:
        """
        Ingest data from Jira integration
        
        Args:
            config: Jira integration config (url, username, token, projects)
            project_id: UUID of the project to ingest data for
            
        Returns:
            Dict with ingestion results
        """
        url = config.get("url")
        username = config.get("username")
        api_token = config.get("token")
        jira_projects = config.get("projects", [])
        
        if not all([url, username, api_token]):
            return {
                "success": False,
                "message": "Jira URL, username, and API token are required"
            }
        
        if not jira_projects:
            return {
                "success": False,
                "message": "No Jira projects selected for ingestion"
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Update integration sync status
            if self.integration:
                self.integration.last_sync_started_at = datetime.utcnow()
                self.integration.sync_status = "in_progress"
                self.db.commit()
            
            # Normalize URL and set API base path
            url = self._normalize_url(url)
            is_cloud = self._is_cloud_instance(url)
            self.api_base = self.CLOUD_API_BASE if is_cloud else self.SERVER_API_BASE
            
            # Set up auth
            auth = aiohttp.BasicAuth(username, api_token)
            
            # Get issues for each project
            total_issues = 0
            processed_issues = 0
            skipped_issues = 0
            project_results = []
            
            # Set up a time window for incremental sync (default: 7 days)
            sync_window = config.get("sync_window", 7)
            time_window = datetime.utcnow() - timedelta(days=sync_window)
            jql_time_clause = f'updated >= "{time_window.strftime("%Y-%m-%d")}"'
            
            for jira_project in jira_projects:
                project_key = jira_project.get("key")
                
                # Build JQL query for getting issues
                jql = f'project = "{project_key}" AND {jql_time_clause}'
                
                project_result = {
                    "project_key": project_key,
                    "project_name": jira_project.get("name"),
                    "issues_total": 0,
                    "issues_processed": 0,
                    "issues_skipped": 0
                }
                
                try:
                    # Search for issues
                    issues_data = await self._search_issues(url, auth, jql)
                    
                    project_result["issues_total"] = len(issues_data)
                    total_issues += len(issues_data)
                    
                    # Process each issue in batches
                    batch_size = 10
                    for i in range(0, len(issues_data), batch_size):
                        batch = issues_data[i:i+batch_size]
                        batch_results = await self._process_issues_batch(url, auth, batch, project_id)
                        
                        processed_issues += batch_results["processed"]
                        skipped_issues += batch_results["skipped"]
                        project_result["issues_processed"] += batch_results["processed"]
                        project_result["issues_skipped"] += batch_results["skipped"]
                    
                    project_results.append(project_result)
                    
                except Exception as e:
                    logger.error(f"Error processing Jira project {project_key}: {str(e)}")
                    project_result["error"] = str(e)
                    project_results.append(project_result)
            
            # Update integration sync status
            if self.integration:
                self.integration.last_sync_completed_at = datetime.utcnow()
                self.integration.sync_status = "completed"
                
                # Schedule next sync (default: 24 hours)
                next_sync_hours = config.get("next_sync_hours", 24)
                self.integration.next_sync_at = datetime.utcnow() + timedelta(hours=next_sync_hours)
                
                self.db.commit()
            
            return {
                "success": True,
                "message": f"Successfully ingested {processed_issues} issues from {len(project_results)} Jira projects",
                "details": {
                    "projects_processed": len(project_results),
                    "total_issues": total_issues,
                    "processed_issues": processed_issues,
                    "skipped_issues": skipped_issues,
                    "project_results": project_results
                }
            }
        
        except Exception as e:
            logger.error(f"Error ingesting Jira data: {str(e)}")
            
            # Update integration sync status on error
            if self.integration:
                self.integration.last_sync_completed_at = datetime.utcnow()
                self.integration.sync_status = "failed"
                self.integration.last_sync_error = str(e)
                self.db.commit()
            
            return {
                "success": False,
                "message": f"Error ingesting Jira data: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None

    async def _search_issues(self, url: str, auth: aiohttp.BasicAuth, jql: str) -> List[Dict[str, Any]]:
        """
        Search for issues in Jira using JQL
        
        Args:
            url: Jira URL
            auth: aiohttp BasicAuth object
            jql: JQL query string
            
        Returns:
            List of issues
        """
        # Initial search with pagination setup
        start_at = 0
        max_results = 50
        all_issues = []
        
        while True:
            endpoint = f"{url}{self.api_base}/search"
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "summary,description,status,created,updated,assignee,reporter,priority,labels,components,comment,issuetype"
            }
            
            async with self.session.get(endpoint, params=params, auth=auth) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Jira API error: {error_text}")
                    raise Exception(f"Jira API error: {error_text}")
                
                search_result = await response.json()
                
                issues = search_result.get("issues", [])
                all_issues.extend(issues)
                
                # Check if we need to paginate further
                total = search_result.get("total", 0)
                if start_at + max_results >= total or not issues:
                    break
                
                start_at += max_results
        
        return all_issues
    
    async def _process_issues_batch(self, url: str, auth: aiohttp.BasicAuth, 
                                   issues: List[Dict[str, Any]], project_id: UUID) -> Dict[str, int]:
        """
        Process a batch of issues
        
        Args:
            url: Jira URL
            auth: aiohttp BasicAuth object
            issues: List of issues to process
            project_id: UUID of the project
            
        Returns:
            Dict with processing results
        """
        processed = 0
        skipped = 0
        
        for issue in issues:
            try:
                # Get issue key and fields
                issue_key = issue.get("key")
                fields = issue.get("fields", {})
                
                # Get basic issue data
                issue_data = {
                    "key": issue_key,
                    "id": issue.get("id"),
                    "summary": fields.get("summary", ""),
                    "description": fields.get("description", ""),
                    "created_at": fields.get("created"),
                    "updated_at": fields.get("updated"),
                    "status": fields.get("status", {}).get("name") if fields.get("status") else None,
                    "issue_type": fields.get("issuetype", {}).get("name") if fields.get("issuetype") else None,
                    "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
                    "labels": fields.get("labels", []),
                    "components": [c.get("name") for c in fields.get("components", [])],
                    "reporter": self._get_user_info(fields.get("reporter")),
                    "assignee": self._get_user_info(fields.get("assignee")),
                }
                
                # Get comments for the issue
                issue_data["comments"] = await self._get_issue_comments(url, auth, issue_key)
                
                # Apply ML importance filter (placeholder for now)
                importance_score = await self._filter_data_importance(issue_data)
                issue_data["importance_score"] = importance_score
                
                # Skip items with very low importance
                if importance_score < 0.2:  # Threshold for "noise"
                    skipped += 1
                    continue
                
                # Prepare data for persistence
                documents = self._prepare_documents_from_issue(issue_data, project_id)
                
                # Persist data to vector database
                await self._persist_data(documents, project_id)
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing issue {issue.get('key')}: {str(e)}")
                skipped += 1
        
        return {"processed": processed, "skipped": skipped}
    
    async def _get_issue_comments(self, url: str, auth: aiohttp.BasicAuth, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get comments for a Jira issue
        
        Args:
            url: Jira URL
            auth: aiohttp BasicAuth object
            issue_key: Jira issue key
            
        Returns:
            List of comments
        """
        endpoint = f"{url}{self.api_base}/issue/{issue_key}/comment"
        
        try:
            async with self.session.get(endpoint, auth=auth) as response:
                if response.status != 200:
                    return []
                
                result = await response.json()
                comments = result.get("comments", [])
                
                formatted_comments = []
                for comment in comments:
                    formatted_comments.append({
                        "id": comment.get("id"),
                        "body": comment.get("body", ""),
                        "created_at": comment.get("created"),
                        "updated_at": comment.get("updated"),
                        "author": self._get_user_info(comment.get("author"))
                    })
                
                return formatted_comments
        except Exception as e:
            logger.error(f"Error getting comments for issue {issue_key}: {str(e)}")
            return []
    
    def _get_user_info(self, user_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Extract user information from Jira user data
        
        Args:
            user_data: Jira user data
            
        Returns:
            Formatted user info or None
        """
        if not user_data:
            return None
        
        return {
            "name": user_data.get("displayName"),
            "email": user_data.get("emailAddress"),
            "account_id": user_data.get("accountId"),
            "avatar_url": user_data.get("avatarUrls", {}).get("48x48") if "avatarUrls" in user_data else None
        }
    
    def _prepare_documents_from_issue(self, issue_data: Dict[str, Any], project_id: UUID) -> List[Dict[str, Any]]:
        """
        Prepare documents from Jira issue data for persistence
        
        Args:
            issue_data: Issue data
            project_id: UUID of the project
            
        Returns:
            List of documents for vector database
        """
        documents = []
        
        # Main issue document
        issue_doc = {
            "id": f"jira-issue-{issue_data['key']}",
            "content": f"{issue_data['summary']}\n\n{issue_data['description']}",
            "metadata": {
                "source": "jira",
                "source_type": "issue",
                "project_id": str(project_id),
                "issue_key": issue_data["key"],
                "issue_id": issue_data["id"],
                "issue_type": issue_data["issue_type"],
                "status": issue_data["status"],
                "priority": issue_data["priority"],
                "created_at": issue_data["created_at"],
                "updated_at": issue_data["updated_at"],
                "labels": issue_data["labels"],
                "components": issue_data["components"],
                "reporter": issue_data["reporter"]["name"] if issue_data["reporter"] else None,
                "assignee": issue_data["assignee"]["name"] if issue_data["assignee"] else None,
                "importance_score": issue_data["importance_score"]
            }
        }
        documents.append(issue_doc)
        
        # Comments as separate documents
        for comment in issue_data.get("comments", []):
            comment_doc = {
                "id": f"jira-comment-{comment['id']}",
                "content": comment["body"],
                "metadata": {
                    "source": "jira",
                    "source_type": "comment",
                    "project_id": str(project_id),
                    "issue_key": issue_data["key"],
                    "comment_id": comment["id"],
                    "created_at": comment["created_at"],
                    "updated_at": comment["updated_at"],
                    "author": comment["author"]["name"] if comment["author"] else None,
                    "importance_score": issue_data["importance_score"] * 0.8  # Slightly less important than the issue itself
                }
            }
            documents.append(comment_doc)
        
        return documents
    
    async def _filter_data_importance(self, data: Dict[str, Any]) -> float:
        """
        Filter data by importance (placeholder for ML model)
        
        Args:
            data: Data to filter
            
        Returns:
            Importance score (0.0 to 1.0)
        """
        # Simple heuristic scoring based on content length, status, etc.
        # This will be replaced with a proper ML model in the future
        
        # Start with a base score
        score = 0.5
        
        # Adjust based on content length
        description_length = len(data.get("description", ""))
        if description_length > 1000:
            score += 0.2
        elif description_length > 500:
            score += 0.1
        elif description_length < 50:
            score -= 0.1
        
        # Adjust based on comments
        comment_count = len(data.get("comments", []))
        if comment_count > 10:
            score += 0.2
        elif comment_count > 5:
            score += 0.1
        
        # Adjust based on status
        status = data.get("status", "").lower()
        if status in ["in progress", "open", "todo"]:
            score += 0.1
        elif status in ["done", "closed", "resolved"]:
            score -= 0.05
        
        # Ensure score is within bounds
        return max(0.0, min(1.0, score))
    
    async def _persist_data(self, documents: List[Dict[str, Any]], project_id: UUID) -> bool:
        """
        Persist data to vector database
        
        Args:
            documents: List of documents to persist
            project_id: UUID of the project
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This is a placeholder that would integrate with the VectorDatabaseService
            # TODO: Implement actual persistence using VectorDatabaseService
            logger.info(f"Would persist {len(documents)} documents for project {project_id}")
            
            # In a real implementation, we would:
            # 1. Get a VectorDatabaseService instance
            # 2. Call its add_documents method
            
            return True
        except Exception as e:
            logger.error(f"Error persisting data: {str(e)}")
            return False
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize Jira URL (remove trailing slashes)
        
        Args:
            url: Jira URL
            
        Returns:
            Normalized URL
        """
        if url.endswith("/"):
            url = url[:-1]
        return url
    
    def _is_cloud_instance(self, url: str) -> bool:
        """
        Determine if Jira instance is cloud or server
        
        Args:
            url: Jira URL
            
        Returns:
            True if cloud instance, False otherwise
        """
        return "atlassian.net" in url.lower()
