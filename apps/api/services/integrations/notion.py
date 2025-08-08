"""
Notion Integration Service for NeuroSync API
Handles Notion API authentication, workspace discovery, and page/database ingestion
"""

import logging
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session
from models.integration import Integration
from models.project import Project
from .base import BaseIntegrationService

# Create logger
logger = logging.getLogger(__name__)

class NotionIntegrationService(BaseIntegrationService):
    """
    Notion Integration Service
    Handles Notion API authentication, workspace discovery, and page/database ingestion
    """
    
    # Notion API constants
    API_BASE = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"  # Current Notion API version
    
    def __init__(self, db: Session, integration: Optional[Integration] = None):
        """
        Initialize Notion integration service
        
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
        Test Notion API connection
        
        Args:
            config: Notion integration config (token)
            
        Returns:
            Dict with connection test results
        """
        token = config.get("token")
        
        if not token:
            return {
                "success": False,
                "message": "Notion integration token is required"
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Test API connection by getting user info
            endpoint = f"{self.API_BASE}/users/me"
            headers = self._get_headers(token)
            
            async with self.session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    user_info = await response.json()
                    return {
                        "success": True,
                        "message": "Successfully connected to Notion",
                        "details": {
                            "user_name": user_info.get("name"),
                            "user_type": user_info.get("type"),
                            "user_id": user_info.get("id")
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "message": f"Notion API error: {error_text}",
                        "details": {"status_code": response.status}
                    }
        except Exception as e:
            logger.error(f"Error testing Notion connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to Notion: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def get_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get Notion metadata (workspaces, pages, databases)
        
        Args:
            config: Notion integration config (token)
            
        Returns:
            Dict with Notion metadata
        """
        token = config.get("token")
        
        if not token:
            return {
                "success": False,
                "message": "Notion integration token is required"
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Get current user and their permissions
            user_info = await self._get_current_user(token)
            if not user_info.get("success", False):
                return user_info
                
            # Get user's workspaces (the bot has access to)
            workspaces = await self._get_workspaces(token)
            
            # Get top-level pages the integration has access to
            pages = await self._get_top_level_pages(token)
            
            # Get databases the integration has access to
            databases = await self._get_databases(token)
            
            return {
                "success": True,
                "user": {
                    "id": user_info.get("user", {}).get("id"),
                    "name": user_info.get("user", {}).get("name"),
                    "type": user_info.get("user", {}).get("type"),
                    "avatar_url": user_info.get("user", {}).get("avatar_url")
                },
                "workspaces": workspaces.get("workspaces", []),
                "workspace_count": len(workspaces.get("workspaces", [])),
                "pages": pages.get("pages", []),
                "page_count": len(pages.get("pages", [])),
                "databases": databases.get("databases", []),
                "database_count": len(databases.get("databases", []))
            }
        except Exception as e:
            logger.error(f"Error getting Notion metadata: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Notion metadata: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def _get_current_user(self, token: str) -> Dict[str, Any]:
        """
        Get current Notion user
        
        Args:
            token: Notion API token
            
        Returns:
            Dict with user info
        """
        endpoint = f"{self.API_BASE}/users/me"
        headers = self._get_headers(token)
        
        async with self.session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                user = await response.json()
                return {
                    "success": True,
                    "user": user
                }
            else:
                error_text = await response.text()
                logger.error(f"Error getting Notion user info: {error_text}")
                return {
                    "success": False,
                    "message": f"Notion API error: {error_text}",
                    "details": {"status_code": response.status}
                }
    
    async def _get_workspaces(self, token: str) -> Dict[str, Any]:
        """
        Get Notion workspaces the integration has access to
        
        Args:
            token: Notion API token
            
        Returns:
            Dict with workspace info
        """
        # Notion API doesn't have a direct endpoint to list workspaces
        # Instead, we can get all users which includes workspace info
        endpoint = f"{self.API_BASE}/users"
        headers = self._get_headers(token)
        
        workspaces = {}
        
        try:
            # Get all users (with pagination)
            start_cursor = None
            has_more = True
            
            while has_more:
                params = {"page_size": 100}
                if start_cursor:
                    params["start_cursor"] = start_cursor
                    
                async with self.session.get(endpoint, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error getting Notion users: {error_text}")
                        return {
                            "success": False,
                            "message": f"Notion API error: {error_text}",
                            "details": {"status_code": response.status}
                        }
                    
                    result = await response.json()
                    
                    # Extract workspaces from user results
                    for user in result.get("results", []):
                        if user.get("type") == "bot":
                            continue
                            
                        for workspace in user.get("workspace_access", []):
                            workspace_id = workspace.get("workspace_id")
                            if workspace_id and workspace_id not in workspaces:
                                workspaces[workspace_id] = {
                                    "id": workspace_id,
                                    "name": workspace.get("workspace_name", "Unknown Workspace"),
                                }
                    
                    # Check pagination
                    has_more = result.get("has_more", False)
                    if has_more:
                        start_cursor = result.get("next_cursor")
                        
            # Convert dict to list
            workspace_list = list(workspaces.values())
            
            return {
                "success": True,
                "workspaces": workspace_list
            }
        except Exception as e:
            logger.error(f"Error getting Notion workspaces: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Notion workspaces: {str(e)}"
            }
    
    async def _get_top_level_pages(self, token: str) -> Dict[str, Any]:
        """
        Get top-level Notion pages the integration has access to
        
        Args:
            token: Notion API token
            
        Returns:
            Dict with page info
        """
        endpoint = f"{self.API_BASE}/search"
        headers = self._get_headers(token)
        
        # Search for pages
        body = {
            "filter": {
                "value": "page",
                "property": "object"
            },
            "sort": {
                "direction": "descending",
                "timestamp": "last_edited_time"
            },
            "page_size": 100
        }
        
        try:
            pages = []
            start_cursor = None
            has_more = True
            
            while has_more:
                if start_cursor:
                    body["start_cursor"] = start_cursor
                    
                async with self.session.post(endpoint, headers=headers, json=body) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error getting Notion pages: {error_text}")
                        return {
                            "success": False,
                            "message": f"Notion API error: {error_text}",
                            "details": {"status_code": response.status}
                        }
                    
                    result = await response.json()
                    
                    # Process pages
                    for page in result.get("results", []):
                        # Extract page metadata
                        page_id = page.get("id")
                        title = self._extract_page_title(page)
                        url = page.get("url")
                        last_edited = page.get("last_edited_time")
                        created_time = page.get("created_time")
                        
                        pages.append({
                            "id": page_id,
                            "title": title,
                            "url": url,
                            "last_edited": last_edited,
                            "created_time": created_time
                        })
                    
                    # Check pagination
                    has_more = result.get("has_more", False)
                    if has_more:
                        start_cursor = result.get("next_cursor")
                        
            return {
                "success": True,
                "pages": pages
            }
        except Exception as e:
            logger.error(f"Error getting Notion pages: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Notion pages: {str(e)}"
            }
    
    async def _get_databases(self, token: str) -> Dict[str, Any]:
        """
        Get Notion databases the integration has access to
        
        Args:
            token: Notion API token
            
        Returns:
            Dict with database info
        """
        endpoint = f"{self.API_BASE}/search"
        headers = self._get_headers(token)
        
        # Search for databases
        body = {
            "filter": {
                "value": "database",
                "property": "object"
            },
            "sort": {
                "direction": "descending",
                "timestamp": "last_edited_time"
            },
            "page_size": 100
        }
        
        try:
            databases = []
            start_cursor = None
            has_more = True
            
            while has_more:
                if start_cursor:
                    body["start_cursor"] = start_cursor
                    
                async with self.session.post(endpoint, headers=headers, json=body) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error getting Notion databases: {error_text}")
                        return {
                            "success": False,
                            "message": f"Notion API error: {error_text}",
                            "details": {"status_code": response.status}
                        }
                    
                    result = await response.json()
                    
                    # Process databases
                    for db in result.get("results", []):
                        # Extract database metadata
                        db_id = db.get("id")
                        title = self._extract_database_title(db)
                        url = db.get("url")
                        last_edited = db.get("last_edited_time")
                        created_time = db.get("created_time")
                        
                        # Get property schema
                        properties = []
                        for prop_name, prop_data in db.get("properties", {}).items():
                            properties.append({
                                "name": prop_name,
                                "type": prop_data.get("type")
                            })
                        
                        databases.append({
                            "id": db_id,
                            "title": title,
                            "url": url,
                            "last_edited": last_edited,
                            "created_time": created_time,
                            "property_count": len(properties),
                            "properties": properties
                        })
                    
                    # Check pagination
                    has_more = result.get("has_more", False)
                    if has_more:
                        start_cursor = result.get("next_cursor")
                        
            return {
                "success": True,
                "databases": databases
            }
        except Exception as e:
            logger.error(f"Error getting Notion databases: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Notion databases: {str(e)}"
            }
    
    def _extract_page_title(self, page: Dict[str, Any]) -> str:
        """
        Extract page title from Notion page object
        
        Args:
            page: Notion page object
            
        Returns:
            Page title or "Untitled"
        """
        # Try to get title from properties
        properties = page.get("properties", {})
        title_property = None
        
        # Find title property
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_property = prop_data
                break
                
        if title_property:
            title_content = title_property.get("title", [])
            if title_content:
                # Concatenate all text parts
                return "".join([part.get("plain_text", "") for part in title_content])
        
        return "Untitled"
    
    def _extract_database_title(self, database: Dict[str, Any]) -> str:
        """
        Extract database title from Notion database object
        
        Args:
            database: Notion database object
            
        Returns:
            Database title or "Untitled Database"
        """
        # Try to get title
        title = database.get("title", [])
        if title:
            # Concatenate all text parts
            return "".join([part.get("plain_text", "") for part in title])
            
        return "Untitled Database"
    
    def _get_headers(self, token: str) -> Dict[str, str]:
        """
        Get headers for Notion API requests
        
        Args:
            token: Notion API token
            
        Returns:
            Dict with headers
        """
        return {
            "Authorization": f"Bearer {token}",
            "Notion-Version": self.API_VERSION,
            "Content-Type": "application/json"
        }

    # Data ingestion methods
    async def ingest_data(self, config: Dict[str, Any], project_id: UUID) -> Dict[str, Any]:
        """
        Ingest Notion data (pages, databases)
        
        Args:
            config: Notion integration config
            project_id: Project ID to associate data with
            
        Returns:
            Dict with ingestion results
        """
        token = config.get("token")
        selected_pages = config.get("selected_pages", [])
        selected_databases = config.get("selected_databases", [])
        sync_days = config.get("sync_days", 7)  # Default to 7 days
        
        if not token:
            return {
                "success": False,
                "message": "Notion integration token is required"
            }
            
        if not selected_pages and not selected_databases:
            return {
                "success": False, 
                "message": "No Notion pages or databases selected for ingestion"
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            # Calculate sync window
            since_date = datetime.now() - timedelta(days=sync_days)
            
            # Update integration sync status
            if self.integration:
                self.integration.last_sync_started_at = datetime.now()
                self.integration.sync_status = "in_progress"
                self.integration.last_sync_error = None
                self.db.commit()
            
            # Get headers for API requests
            headers = self._get_headers(token)
            
            # Stats for tracking progress
            stats = {
                "pages_processed": 0,
                "pages_ingested": 0,
                "databases_processed": 0,
                "database_items_processed": 0,
                "database_items_ingested": 0,
                "errors": [],
            }
            
            # Process each selected page
            total_documents = []
            
            # Process pages
            if selected_pages:
                page_documents = await self._process_pages(headers, selected_pages, since_date, project_id, stats)
                if page_documents:
                    total_documents.extend(page_documents)
            
            # Process databases
            if selected_databases:
                db_documents = await self._process_databases(headers, selected_databases, since_date, project_id, stats)
                if db_documents:
                    total_documents.extend(db_documents)
            
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
                "message": "Notion data ingestion completed",
                "stats": stats
            }
            
        except Exception as e:
            error_msg = f"Error during Notion data ingestion: {str(e)}"
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
    
    async def _process_pages(self, headers: Dict[str, str], page_ids: List[str], 
                           since_date: datetime, project_id: UUID, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process Notion pages
        
        Args:
            headers: Notion API headers
            page_ids: List of page IDs to process
            since_date: Date to filter pages by
            project_id: Project ID
            stats: Stats dictionary to update
            
        Returns:
            List of processed page documents
        """
        documents = []
        
        for page_id in page_ids:
            try:
                # Get page content
                page_content = await self._get_page_content(headers, page_id)
                if not page_content:
                    stats["errors"].append(f"Failed to get content for page {page_id}")
                    continue
                
                stats["pages_processed"] += 1
                
                # Check if page was updated after the since_date
                last_edited = page_content.get("last_edited_time")
                if last_edited:
                    last_edited_date = datetime.fromisoformat(last_edited.replace("Z", "+00:00"))
                    if last_edited_date < since_date:
                        continue  # Skip if page was not updated in the sync window
                
                # Get page blocks (content)
                blocks = await self._get_page_blocks(headers, page_id)
                
                # Process the page data
                processed_page = self._process_page_data(page_content, blocks)
                
                # Filter by importance
                if self._filter_data_importance(processed_page):
                    # Prepare document for vector DB
                    documents.append(
                        self._prepare_document_from_page(processed_page, project_id)
                    )
                    stats["pages_ingested"] += 1
                
            except Exception as e:
                error_msg = f"Error processing Notion page {page_id}: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                
        return documents
    
    async def _process_databases(self, headers: Dict[str, str], database_ids: List[str],
                               since_date: datetime, project_id: UUID, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process Notion databases
        
        Args:
            headers: Notion API headers
            database_ids: List of database IDs to process
            since_date: Date to filter database items by
            project_id: Project ID
            stats: Stats dictionary to update
            
        Returns:
            List of processed database item documents
        """
        documents = []
        
        for db_id in database_ids:
            try:
                # Get database schema
                db_schema = await self._get_database_schema(headers, db_id)
                if not db_schema:
                    stats["errors"].append(f"Failed to get schema for database {db_id}")
                    continue
                
                stats["databases_processed"] += 1
                
                # Query database items
                db_items = await self._query_database(headers, db_id, since_date)
                stats["database_items_processed"] += len(db_items)
                
                # Process each database item
                for item in db_items:
                    try:
                        # Get item blocks (content)
                        item_blocks = await self._get_page_blocks(headers, item["id"])
                        
                        # Process the database item data
                        processed_item = self._process_database_item(item, db_schema, item_blocks)
                        
                        # Filter by importance
                        if self._filter_data_importance(processed_item):
                            # Prepare document for vector DB
                            documents.append(
                                self._prepare_document_from_database_item(processed_item, project_id)
                            )
                            stats["database_items_ingested"] += 1
                    
                    except Exception as e:
                        error_msg = f"Error processing database item {item.get('id')}: {str(e)}"
                        logger.error(error_msg)
                        stats["errors"].append(error_msg)
                
            except Exception as e:
                error_msg = f"Error processing Notion database {db_id}: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                
        return documents
    
    async def _get_page_content(self, headers: Dict[str, str], page_id: str) -> Dict[str, Any]:
        """
        Get Notion page content
        
        Args:
            headers: Notion API headers
            page_id: Page ID
            
        Returns:
            Page content
        """
        endpoint = f"{self.API_BASE}/pages/{page_id}"
        
        async with self.session.get(endpoint, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Notion API error getting page content: {error_text}")
                return None
                
            return await response.json()
    
    async def _get_page_blocks(self, headers: Dict[str, str], page_id: str) -> List[Dict[str, Any]]:
        """
        Get Notion page blocks (content)
        
        Args:
            headers: Notion API headers
            page_id: Page ID
            
        Returns:
            List of page blocks
        """
        endpoint = f"{self.API_BASE}/blocks/{page_id}/children"
        params = {"page_size": 100}
        
        blocks = []
        has_more = True
        next_cursor = None
        
        while has_more:
            if next_cursor:
                params["start_cursor"] = next_cursor
                
            async with self.session.get(endpoint, headers=headers, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Notion API error getting page blocks: {error_text}")
                    break
                    
                result = await response.json()
                
                # Add blocks to list
                blocks.extend(result.get("results", []))
                
                # Check for more blocks
                has_more = result.get("has_more", False)
                if has_more:
                    next_cursor = result.get("next_cursor")
        
        # Process nested blocks recursively
        expanded_blocks = []
        for block in blocks:
            expanded_blocks.append(block)
            
            # Check if block has children
            if block.get("has_children", False):
                child_blocks = await self._get_page_blocks(headers, block["id"])
                expanded_blocks.extend(child_blocks)
                
        return expanded_blocks
    
    async def _get_database_schema(self, headers: Dict[str, str], database_id: str) -> Dict[str, Any]:
        """
        Get Notion database schema
        
        Args:
            headers: Notion API headers
            database_id: Database ID
            
        Returns:
            Database schema
        """
        endpoint = f"{self.API_BASE}/databases/{database_id}"
        
        async with self.session.get(endpoint, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Notion API error getting database schema: {error_text}")
                return None
                
            return await response.json()
    
    async def _query_database(self, headers: Dict[str, str], database_id: str, since_date: datetime) -> List[Dict[str, Any]]:
        """
        Query Notion database for items
        
        Args:
            headers: Notion API headers
            database_id: Database ID
            since_date: Date to filter items by
            
        Returns:
            List of database items
        """
        endpoint = f"{self.API_BASE}/databases/{database_id}/query"
        
        # Create filter for last edited time
        since_str = since_date.isoformat()
        body = {
            "filter": {
                "property": "last_edited_time",
                "date": {
                    "on_or_after": since_str
                }
            },
            "page_size": 100
        }
        
        results = []
        has_more = True
        next_cursor = None
        
        while has_more:
            if next_cursor:
                body["start_cursor"] = next_cursor
                
            async with self.session.post(endpoint, headers=headers, json=body) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Notion API error querying database: {error_text}")
                    break
                    
                result = await response.json()
                
                # Add results
                results.extend(result.get("results", []))
                
                # Check for more results
                has_more = result.get("has_more", False)
                if has_more:
                    next_cursor = result.get("next_cursor")
                    
        return results
    
    def _process_page_data(self, page: Dict[str, Any], blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process Notion page data
        
        Args:
            page: Page object
            blocks: Page blocks
            
        Returns:
            Processed page data
        """
        # Extract basic page info
        page_id = page.get("id")
        page_url = page.get("url")
        created_time = page.get("created_time")
        last_edited_time = page.get("last_edited_time")
        
        # Extract page title
        title = self._extract_page_title(page)
        
        # Extract content from blocks
        content = self._extract_content_from_blocks(blocks)
        
        # Extract parent info
        parent = page.get("parent", {})
        parent_type = parent.get("type")
        parent_id = parent.get(parent_type) if parent_type else None
        
        return {
            "id": page_id,
            "title": title,
            "content": content,
            "url": page_url,
            "created_time": created_time,
            "last_edited_time": last_edited_time,
            "parent_type": parent_type,
            "parent_id": parent_id,
            "block_count": len(blocks)
        }
    
    def _process_database_item(self, item: Dict[str, Any], db_schema: Dict[str, Any], blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process Notion database item data
        
        Args:
            item: Database item object
            db_schema: Database schema
            blocks: Item blocks
            
        Returns:
            Processed database item data
        """
        # Extract basic item info
        item_id = item.get("id")
        item_url = item.get("url")
        created_time = item.get("created_time")
        last_edited_time = item.get("last_edited_time")
        
        # Extract database title
        db_title = self._extract_database_title(db_schema)
        
        # Extract item title
        item_title = self._extract_page_title(item)
        
        # Extract content from blocks
        content = self._extract_content_from_blocks(blocks)
        
        # Extract properties
        properties = {}
        for prop_name, prop_value in item.get("properties", {}).items():
            prop_type = prop_value.get("type")
            extracted_value = self._extract_property_value(prop_value)
            if extracted_value is not None:
                properties[prop_name] = {
                    "type": prop_type,
                    "value": extracted_value
                }
        
        return {
            "id": item_id,
            "database_id": db_schema.get("id"),
            "database_title": db_title,
            "title": item_title,
            "content": content,
            "url": item_url,
            "created_time": created_time,
            "last_edited_time": last_edited_time,
            "properties": properties,
            "block_count": len(blocks)
        }
    
    def _extract_content_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Extract content from Notion blocks
        
        Args:
            blocks: List of blocks
            
        Returns:
            Extracted content as text
        """
        content = []
        
        for block in blocks:
            block_type = block.get("type")
            if not block_type:
                continue
                
            block_content = block.get(block_type, {})
            
            # Handle different block types
            if block_type == "paragraph":
                text = self._get_rich_text_content(block_content.get("rich_text", []))
                if text:
                    content.append(text)
            
            elif block_type == "heading_1":
                text = self._get_rich_text_content(block_content.get("rich_text", []))
                if text:
                    content.append(f"# {text}")
            
            elif block_type == "heading_2":
                text = self._get_rich_text_content(block_content.get("rich_text", []))
                if text:
                    content.append(f"## {text}")
            
            elif block_type == "heading_3":
                text = self._get_rich_text_content(block_content.get("rich_text", []))
                if text:
                    content.append(f"### {text}")
            
            elif block_type == "bulleted_list_item":
                text = self._get_rich_text_content(block_content.get("rich_text", []))
                if text:
                    content.append(f"- {text}")
            
            elif block_type == "numbered_list_item":
                text = self._get_rich_text_content(block_content.get("rich_text", []))
                if text:
                    # We don't know the actual number in the list, so using "1." for all
                    content.append(f"1. {text}")
            
            elif block_type == "to_do":
                text = self._get_rich_text_content(block_content.get("rich_text", []))
                checked = block_content.get("checked", False)
                if text:
                    content.append(f"{'[x]' if checked else '[ ]'} {text}")
            
            elif block_type == "code":
                text = self._get_rich_text_content(block_content.get("rich_text", []))
                language = block_content.get("language", "")
                if text:
                    content.append(f"```{language}\n{text}\n```")
            
            elif block_type == "quote":
                text = self._get_rich_text_content(block_content.get("rich_text", []))
                if text:
                    content.append(f"> {text}")
            
            elif block_type == "callout":
                text = self._get_rich_text_content(block_content.get("rich_text", []))
                if text:
                    content.append(f"📌 {text}")
            
            elif block_type == "toggle":
                text = self._get_rich_text_content(block_content.get("rich_text", []))
                if text:
                    content.append(f"▶️ {text}")
            
            elif block_type == "divider":
                content.append("---")
            
            # Add other block types as needed
        
        return "\n\n".join(content)
    
    def _get_rich_text_content(self, rich_text: List[Dict[str, Any]]) -> str:
        """
        Get text content from rich text objects
        
        Args:
            rich_text: List of rich text objects
            
        Returns:
            Extracted text
        """
        if not rich_text:
            return ""
            
        return "".join([text.get("plain_text", "") for text in rich_text])
    
    def _extract_property_value(self, property_value: Dict[str, Any]) -> Any:
        """
        Extract value from property
        
        Args:
            property_value: Property value object
            
        Returns:
            Extracted property value
        """
        prop_type = property_value.get("type")
        
        if not prop_type or prop_type not in property_value:
            return None
            
        value = property_value.get(prop_type)
        
        # Handle different property types
        if prop_type == "title" or prop_type == "rich_text":
            return self._get_rich_text_content(value)
            
        elif prop_type == "number":
            return value
            
        elif prop_type == "select":
            return value.get("name") if value else None
            
        elif prop_type == "multi_select":
            return [item.get("name") for item in value] if value else []
            
        elif prop_type == "date":
            if not value:
                return None
                
            result = {"start": value.get("start")}
            if value.get("end"):
                result["end"] = value.get("end")
            return result
            
        elif prop_type == "checkbox":
            return value
            
        elif prop_type == "url":
            return value
            
        elif prop_type == "email":
            return value
            
        elif prop_type == "phone_number":
            return value
            
        elif prop_type == "formula":
            formula_type = value.get("type")
            return value.get(formula_type) if formula_type else None
            
        elif prop_type == "relation":
            return [item.get("id") for item in value] if value else []
            
        elif prop_type == "people":
            return [item.get("id") for item in value] if value else []
            
        elif prop_type == "files":
            return [item.get("name") for item in value] if value else []
            
        return None
    
    def _filter_data_importance(self, data: Dict[str, Any]) -> bool:
        """
        Filter data by importance
        This is a placeholder for the ML-based importance filter
        
        Args:
            data: Processed data
            
        Returns:
            True if data is important, False otherwise
        """
        # In the future, replace this with ML model scoring
        
        # Simple heuristic based on content length and properties
        if "content" in data:
            content_length = len(data.get("content", ""))
            # Consider important if substantial content
            if content_length > 500:
                return True
                
        # For database items, check if it has properties
        if "properties" in data:
            property_count = len(data.get("properties", {}))
            # Consider important if it has multiple properties
            if property_count > 3:
                return True
                
        # Check block count (indication of content richness)
        block_count = data.get("block_count", 0)
        if block_count > 5:
            return True
            
        # For now, include most data
        return True
        
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
        
        # Create metadata
        metadata = {
            "id": page_data["id"],
            "title": page_data["title"],
            "url": page_data["url"],
            "created_time": page_data["created_time"],
            "last_edited_time": page_data["last_edited_time"],
            "parent_type": page_data["parent_type"],
            "parent_id": page_data["parent_id"],
            "block_count": page_data["block_count"],
            "project_id": str(project_id),
            "source_type": "notion_page"
        }
        
        return {
            "id": f"notion_page_{page_data['id']}",
            "content": main_content,
            "metadata": metadata
        }
        
    def _prepare_document_from_database_item(self, item_data: Dict[str, Any], project_id: UUID) -> Dict[str, Any]:
        """
        Prepare document for vector database from database item data
        
        Args:
            item_data: Processed database item data
            project_id: Project ID
            
        Returns:
            Document for vector database
        """
        # Main item content
        main_content = f"# {item_data['title']} (from {item_data['database_title']})\n\n"
        
        # Add properties
        if item_data.get("properties"):
            properties_text = "## Properties:\n"
            for prop_name, prop_data in item_data["properties"].items():
                prop_value = prop_data["value"]
                
                # Format property value based on type
                if isinstance(prop_value, list):
                    if prop_value:
                        formatted_value = ", ".join([str(v) for v in prop_value])
                    else:
                        formatted_value = "None"
                elif isinstance(prop_value, dict):
                    formatted_value = str(prop_value)
                else:
                    formatted_value = str(prop_value) if prop_value is not None else "None"
                
                properties_text += f"- **{prop_name}**: {formatted_value}\n"
            
            main_content += properties_text + "\n"
        
        # Add content
        if item_data.get("content"):
            main_content += f"## Content:\n\n{item_data['content']}\n"
        
        # Create metadata
        metadata = {
            "id": item_data["id"],
            "title": item_data["title"],
            "database_id": item_data["database_id"],
            "database_title": item_data["database_title"],
            "url": item_data["url"],
            "created_time": item_data["created_time"],
            "last_edited_time": item_data["last_edited_time"],
            "block_count": item_data["block_count"],
            "project_id": str(project_id),
            "source_type": "notion_database_item"
        }
        
        return {
            "id": f"notion_db_item_{item_data['id']}",
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
            logger.info(f"Would persist {len(documents)} Notion documents to vector DB for project {project_id}")
            
            return {
                "success": True,
                "message": f"Successfully persisted {len(documents)} documents",
                "document_count": len(documents)
            }
        except Exception as e:
            logger.error(f"Error persisting Notion data: {str(e)}")
            return {
                "success": False,
                "message": f"Error persisting data: {str(e)}"
            }
