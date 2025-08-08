"""
Confluence Integration Service for NeuroSync API
Handles Confluence API authentication, space discovery, and page ingestion
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

class ConfluenceIntegrationService(BaseIntegrationService):
    """
    Confluence Integration Service
    Handles Confluence API authentication, space discovery, and page ingestion
    """
    
    # Default API paths
    CLOUD_API_BASE = "/rest/api"
    SERVER_API_BASE = "/rest/api"
    
    def __init__(self, db: Session, integration: Optional[Integration] = None):
        """
        Initialize Confluence integration service
        
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
        Test Confluence API connection
        
        Args:
            config: Confluence integration config (url, username, token)
            
        Returns:
            Dict with connection test results
        """
        url = config.get("url")
        username = config.get("username")
        api_token = config.get("token")
        
        if not all([url, username, api_token]):
            return {
                "success": False,
                "message": "Confluence URL, username, and API token are required"
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
            
            # Test API connection by getting space info
            endpoint = f"{url}{self.api_base}/space"
            auth = aiohttp.BasicAuth(username, api_token)
            
            async with self.session.get(endpoint, auth=auth) as response:
                if response.status == 200:
                    space_info = await response.json()
                    return {
                        "success": True,
                        "message": "Successfully connected to Confluence",
                        "details": {
                            "spaces_found": space_info.get("size", 0),
                            "is_cloud": is_cloud
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "message": f"Confluence API error: {error_text}",
                        "details": {"status_code": response.status}
                    }
        except Exception as e:
            logger.error(f"Error testing Confluence connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to Confluence: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def get_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get Confluence metadata (spaces, pages)
        
        Args:
            config: Confluence integration config (url, username, token)
            
        Returns:
            Dict with Confluence metadata
        """
        url = config.get("url")
        username = config.get("username")
        api_token = config.get("token")
        
        if not all([url, username, api_token]):
            return {
                "success": False,
                "message": "Confluence URL, username, and API token are required"
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
            
            # Get spaces
            endpoint = f"{url}{self.api_base}/space"
            params = {"limit": 100, "expand": "description.plain"}
            auth = aiohttp.BasicAuth(username, api_token)
            
            spaces = []
            start = 0
            
            while True:
                params["start"] = start
                async with self.session.get(endpoint, params=params, auth=auth) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "message": f"Confluence API error: {error_text}",
                            "details": {"status_code": response.status}
                        }
                    
                    result = await response.json()
                    spaces.extend(result.get("results", []))
                    
                    # Check if we need to paginate
                    size = result.get("size", 0)
                    limit = result.get("limit", 100)
                    if size < limit or not result.get("results"):
                        break
                    
                    start += limit
            
            # Format space data
            formatted_spaces = []
            for space in spaces:
                formatted_spaces.append({
                    "id": space.get("id"),
                    "key": space.get("key"),
                    "name": space.get("name"),
                    "type": space.get("type"),
                    "description": space.get("description", {}).get("plain", {}).get("value", ""),
                    "url": f"{url}/spaces/{space.get('key')}",
                    "icon": space.get("icon", {}).get("path") if space.get("icon") else None
                })
            
            # Get current user info
            endpoint = f"{url}{self.api_base}/user/current"
            async with self.session.get(endpoint, auth=auth) as response:
                if response.status != 200:
                    user_data = {"error": "Could not retrieve user information"}
                else:
                    user_data = await response.json()
            
            return {
                "success": True,
                "user": {
                    "display_name": user_data.get("displayName"),
                    "email": user_data.get("email"),
                    "account_id": user_data.get("accountId"),
                    "is_admin": user_data.get("type") == "admin"
                },
                "spaces": formatted_spaces,
                "space_count": len(formatted_spaces),
                "is_cloud": is_cloud
            }
        except Exception as e:
            logger.error(f"Error getting Confluence metadata: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Confluence metadata: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def ingest_data(self, config: Dict[str, Any], project_id: UUID) -> Dict[str, Any]:
        """
        Ingest Confluence data (spaces, pages)
        
        Args:
            config: Confluence integration config
            project_id: Project ID to associate data with
            
        Returns:
            Dict with ingestion results
        """
        url = config.get("url")
        username = config.get("username")
        api_token = config.get("token")
        selected_spaces = config.get("selected_spaces", [])
        sync_days = config.get("sync_days", 7)  # Default to 7 days
        
        if not all([url, username, api_token]):
            return {
                "success": False,
                "message": "Confluence URL, username, and API token are required"
            }
            
        if not selected_spaces:
            return {
                "success": False, 
                "message": "No Confluence spaces selected for ingestion"
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            # Normalize URL and determine instance type
            url = self._normalize_url(url)
            is_cloud = self._is_cloud_instance(url)
            self.api_base = self.CLOUD_API_BASE if is_cloud else self.SERVER_API_BASE
            
            # Calculate sync window
            since_date = datetime.now() - timedelta(days=sync_days)
            since_str = since_date.strftime("%Y-%m-%d")
            
            # Prepare auth
            auth = aiohttp.BasicAuth(username, api_token)
            
            # Update integration sync status
            if self.integration:
                self.integration.last_sync_started_at = datetime.now()
                self.integration.sync_status = "in_progress"
                self.integration.last_sync_error = None
                self.db.commit()
            
            # Stats for tracking progress
            stats = {
                "spaces_processed": 0,
                "pages_processed": 0,
                "pages_ingested": 0,
                "errors": [],
            }
            
            # Process each selected space
            total_documents = []
            for space_key in selected_spaces:
                try:
                    # Get pages in the space
                    space_pages = await self._get_space_pages(url, space_key, since_str, auth)
                    stats["spaces_processed"] += 1
                    stats["pages_processed"] += len(space_pages)
                    
                    # Process pages in batches
                    for page_batch in self._chunk_list(space_pages, 10):  # Process 10 pages at a time
                        page_documents = []
                        for page in page_batch:
                            # Get page content with expanded body
                            page_content = await self._get_page_content(url, page["id"], auth)
                            if not page_content:
                                stats["errors"].append(f"Failed to get content for page {page['id']}")
                                continue
                                
                            # Get page comments
                            page_comments = await self._get_page_comments(url, page["id"], auth)
                            
                            # Process page data
                            processed_page = self._process_page(page, page_content, page_comments, space_key, url)
                            
                            # Check if the page data is important
                            if self._filter_data_importance(processed_page):
                                # Prepare document for vector DB
                                page_documents.append(
                                    self._prepare_document_from_page(processed_page, project_id)
                                )
                                stats["pages_ingested"] += 1
                        
                        # Add to total documents
                        if page_documents:
                            total_documents.extend(page_documents)
                
                except Exception as e:
                    error_msg = f"Error processing Confluence space {space_key}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            # Persist documents to vector database
            if total_documents:
                persist_result = await self._persist_data(total_documents, project_id)
                if not persist_result.get("success", False):
                    stats["errors"].append(f"Error persisting data: {persist_result.get('message')}")
            
            # Update integration status
            if self.integration:
                self.integration.last_sync_completed_at = datetime.now()
                self.integration.sync_status = "completed" if not stats["errors"] else "completed_with_errors"
                self.integration.last_sync_error = "\n".join(stats["errors"]) if stats["errors"] else None
                self.integration.last_sync_metrics = stats
                self.db.commit()
            
            return {
                "success": True,
                "message": "Confluence data ingestion completed",
                "stats": stats
            }
            
        except Exception as e:
            error_msg = f"Error during Confluence data ingestion: {str(e)}"
            logger.error(error_msg)
            
            # Update integration status
            if self.integration:
                self.integration.last_sync_completed_at = datetime.now()
                self.integration.sync_status = "failed"
                self.integration.last_sync_error = error_msg
                self.db.commit()
                
            return {
                "success": False,
                "message": error_msg
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def _get_space_pages(self, url: str, space_key: str, since_str: str, auth: aiohttp.BasicAuth) -> List[Dict[str, Any]]:
        """
        Get all pages in a Confluence space, optionally filtered by update date
        
        Args:
            url: Confluence URL
            space_key: Space key
            since_str: Date string for filtering (YYYY-MM-DD)
            auth: Authentication object
            
        Returns:
            List of page objects
        """
        endpoint = f"{url}{self.api_base}/content"
        params = {
            "spaceKey": space_key,
            "type": "page",
            "status": "current",
            "expand": "version",
            "limit": 50,
        }
        
        # Add date filter if specified
        if since_str:
            params["lastModified"] = f">= {since_str}"
            
        pages = []
        start = 0
        
        while True:
            params["start"] = start
            async with self.session.get(endpoint, params=params, auth=auth) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Confluence API error getting pages: {error_text}")
                    break
                
                result = await response.json()
                pages.extend(result.get("results", []))
                
                # Check if we need to paginate
                size = result.get("size", 0)
                limit = result.get("limit", 50)
                if size < limit or not result.get("results"):
                    break
                
                start += limit
                
        return pages
    
    async def _get_page_content(self, url: str, page_id: str, auth: aiohttp.BasicAuth) -> Dict[str, Any]:
        """
        Get detailed page content with body and metadata
        
        Args:
            url: Confluence URL
            page_id: Page ID
            auth: Authentication object
            
        Returns:
            Page content object with body and metadata
        """
        endpoint = f"{url}{self.api_base}/content/{page_id}"
        params = {
            "expand": "body.storage,version,ancestors,space,history,metadata.labels"
        }
        
        async with self.session.get(endpoint, params=params, auth=auth) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Confluence API error getting page content: {error_text}")
                return None
            
            return await response.json()
    
    async def _get_page_comments(self, url: str, page_id: str, auth: aiohttp.BasicAuth) -> List[Dict[str, Any]]:
        """
        Get comments for a page
        
        Args:
            url: Confluence URL
            page_id: Page ID
            auth: Authentication object
            
        Returns:
            List of comment objects
        """
        endpoint = f"{url}{self.api_base}/content/{page_id}/child/comment"
        params = {
            "expand": "body.storage,version,ancestors,metadata.labels",
            "limit": 25
        }
        
        comments = []
        start = 0
        
        while True:
            params["start"] = start
            async with self.session.get(endpoint, params=params, auth=auth) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Confluence API error getting comments: {error_text}")
                    break
                
                result = await response.json()
                comments.extend(result.get("results", []))
                
                # Check if we need to paginate
                size = result.get("size", 0)
                limit = result.get("limit", 25)
                if size < limit or not result.get("results"):
                    break
                
                start += limit
                
        return comments
    
    def _process_page(self, page: Dict[str, Any], page_content: Dict[str, Any], comments: List[Dict[str, Any]], 
                     space_key: str, base_url: str) -> Dict[str, Any]:
        """
        Process page data into a normalized format
        
        Args:
            page: Basic page data
            page_content: Detailed page content
            comments: Page comments
            space_key: Space key
            base_url: Base Confluence URL
            
        Returns:
            Normalized page data
        """
        # Get basic page info
        page_id = page.get("id")
        page_title = page.get("title", "")
        
        # Extract content from expanded page content
        body_content = page_content.get("body", {}).get("storage", {}).get("value", "")
        
        # Get version and history info
        version = page_content.get("version", {}).get("number", 1)
        created_at = page_content.get("history", {}).get("createdDate")
        updated_at = page_content.get("version", {}).get("when")
        
        # Process ancestor path
        ancestors = page_content.get("ancestors", [])
        ancestor_path = " > ".join([a.get("title", "") for a in ancestors])
        
        # Get space info
        space_info = page_content.get("space", {})
        space_name = space_info.get("name", "")
        
        # Process labels
        labels = []
        labels_data = page_content.get("metadata", {}).get("labels", {}).get("results", [])
        for label in labels_data:
            labels.append(label.get("name", ""))
        
        # Process comments
        processed_comments = []
        for comment in comments:
            processed_comments.append({
                "id": comment.get("id"),
                "content": comment.get("body", {}).get("storage", {}).get("value", ""),
                "author": comment.get("history", {}).get("createdBy", {}).get("displayName", ""),
                "created_at": comment.get("history", {}).get("createdDate"),
                "updated_at": comment.get("version", {}).get("when")
            })
        
        # Create page URL
        page_url = f"{base_url}/spaces/{space_key}/pages/{page_id}"
        
        return {
            "id": page_id,
            "title": page_title,
            "content": body_content,
            "version": version,
            "created_at": created_at,
            "updated_at": updated_at,
            "space_key": space_key,
            "space_name": space_name,
            "ancestor_path": ancestor_path,
            "url": page_url,
            "labels": labels,
            "comments": processed_comments,
            "comment_count": len(processed_comments)
        }
    
    def _filter_data_importance(self, page_data: Dict[str, Any]) -> bool:
        """
        Filter page data by importance
        This is a placeholder for the ML-based importance filter
        
        Args:
            page_data: Processed page data
            
        Returns:
            True if page is important, False otherwise
        """
        # In the future, replace this with ML model scoring
        
        # Simple heuristic: Content length, comments, recency, and labels
        content_length = len(page_data.get("content", ""))
        comment_count = len(page_data.get("comments", []))
        has_labels = len(page_data.get("labels", [])) > 0
        
        # Consider a page important if any of these conditions are met:
        # - Page has substantial content
        # - Page has comments
        # - Page has labels (indicating it's been categorized)
        return content_length > 500 or comment_count > 0 or has_labels
        
    def _prepare_document_from_page(self, page_data: Dict[str, Any], project_id: UUID) -> Dict[str, Any]:
        """
        Prepare document for vector database from page data
        
        Args:
            page_data: Processed page data
            project_id: Project ID
            
        Returns:
            Document for vector database
        """
        # Main page content
        main_content = f"# {page_data['title']}\n\n{page_data['content']}"
        
        # Add comments
        if page_data.get("comments"):
            comments_text = "\n\n## Comments:\n"
            for comment in page_data["comments"]:
                comments_text += f"\n**{comment['author']} ({comment['created_at']})**: {comment['content']}\n"
            main_content += comments_text
        
        # Create metadata
        metadata = {
            "id": page_data["id"],
            "title": page_data["title"],
            "space_key": page_data["space_key"],
            "space_name": page_data["space_name"],
            "url": page_data["url"],
            "created_at": page_data["created_at"],
            "updated_at": page_data["updated_at"],
            "version": page_data["version"],
            "labels": page_data["labels"],
            "ancestor_path": page_data["ancestor_path"],
            "project_id": str(project_id),
            "source_type": "confluence",
            "comment_count": page_data["comment_count"]
        }
        
        return {
            "id": f"confluence_page_{page_data['id']}",
            "content": main_content,
            "metadata": metadata
        }
        
    async def _persist_data(self, documents: List[Dict[str, Any]], project_id: UUID) -> Dict[str, Any]:
        """
        Persist data to vector database
        This is a placeholder for actual vector DB integration
        
        Args:
            documents: List of documents to persist
            project_id: Project ID
            
        Returns:
            Dict with persistence results
        """
        try:
            # TODO: Integrate with VectorDatabaseService
            # For now, just log the document count
            logger.info(f"Would persist {len(documents)} Confluence documents to vector DB for project {project_id}")
            
            return {
                "success": True,
                "message": f"Successfully persisted {len(documents)} documents",
                "document_count": len(documents)
            }
        except Exception as e:
            logger.error(f"Error persisting Confluence data: {str(e)}")
            return {
                "success": False,
                "message": f"Error persisting data: {str(e)}"
            }
            
    def _chunk_list(self, lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """
        Split a list into chunks of specified size
        
        Args:
            lst: List to chunk
            chunk_size: Size of each chunk
            
        Returns:
            List of chunks
        """
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize Confluence URL (remove trailing slashes)
        
        Args:
            url: Confluence URL
            
        Returns:
            Normalized URL
        """
        if url.endswith("/"):
            url = url[:-1]
        return url
    
    def _is_cloud_instance(self, url: str) -> bool:
        """
        Determine if Confluence instance is cloud or server
        
        Args:
            url: Confluence URL
            
        Returns:
            True if cloud instance, False otherwise
        """
        return "atlassian.net" in url.lower()
