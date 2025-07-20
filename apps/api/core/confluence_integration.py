"""
Confluence Integration Service for NeuroSync
Handles Confluence API connectivity, page ingestion, space management, and content processing
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import base64
import json
from concurrent.futures import ThreadPoolExecutor
import re
from urllib.parse import urljoin, quote

from .file_processing import FileProcessingService
from .vector_db import VectorDatabase
from .knowledge_graph import KnowledgeGraphBuilder
from .data_importance_filter import DataImportanceFilter

logger = logging.getLogger(__name__)

class ConfluenceIntegrationService:
    """
    Production-ready Confluence integration service for NeuroSync
    
    Features:
    - Confluence Cloud and Server API support
    - Space discovery and page ingestion
    - Content hierarchy understanding
    - Attachment processing
    - Version tracking and incremental sync
    - Integration with vector DB and knowledge graph
    """
    
    def __init__(self):
        self.file_processor = FileProcessingService()
        self.vector_db = VectorDatabase()
        self.knowledge_graph = KnowledgeGraphBuilder()
        self.importance_filter = DataImportanceFilter()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # API configuration
        self.api_version = "rest/api"
        self.content_api_version = "rest/api/content"
        self.session_timeout = aiohttp.ClientTimeout(total=30)
        
        # Processing limits
        self.max_page_size = 5 * 1024 * 1024  # 5MB
        self.batch_size = 50
        self.max_attachment_size = 10 * 1024 * 1024  # 10MB
        
        # Content filters
        self.excluded_content_types = ['application/octet-stream']
        self.supported_attachment_types = [
            'application/pdf', 'text/plain', 'text/markdown',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
    
    async def test_connection(self, confluence_url: str, email: str, api_token: str) -> Dict[str, Any]:
        """
        Test Confluence API connection and validate credentials
        
        Args:
            confluence_url: Confluence instance URL
            email: User email for authentication
            api_token: API token for authentication
            
        Returns:
            Dict containing connection test results
        """
        try:
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                # Create basic auth header
                auth_string = f"{email}:{api_token}"
                auth_header = base64.b64encode(auth_string.encode()).decode()
                
                headers = {
                    'Authorization': f'Basic {auth_header}',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
                
                # Test connection with user info endpoint
                url = urljoin(confluence_url, f"{self.api_version}/user/current")
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        
                        # Get server info
                        server_url = urljoin(confluence_url, f"{self.api_version}/serverInfo")
                        async with session.get(server_url, headers=headers) as server_response:
                            server_info = await server_response.json() if server_response.status == 200 else {}
                        
                        return {
                            'status': 'success',
                            'user': {
                                'username': user_data.get('username'),
                                'displayName': user_data.get('displayName'),
                                'email': user_data.get('email')
                            },
                            'server': {
                                'baseUrl': server_info.get('baseUrl'),
                                'version': server_info.get('version'),
                                'buildNumber': server_info.get('buildNumber')
                            }
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Authentication failed: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Confluence connection test failed: {str(e)}")
            raise Exception(f"Connection test failed: {str(e)}")
    
    async def get_spaces(self, confluence_url: str, email: str, api_token: str, 
                        space_keys: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get Confluence spaces accessible to the user
        
        Args:
            confluence_url: Confluence instance URL
            email: User email for authentication
            api_token: API token for authentication
            space_keys: Optional list of specific space keys to retrieve
            
        Returns:
            List of space information dictionaries
        """
        try:
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                auth_string = f"{email}:{api_token}"
                auth_header = base64.b64encode(auth_string.encode()).decode()
                
                headers = {
                    'Authorization': f'Basic {auth_header}',
                    'Accept': 'application/json'
                }
                
                spaces = []
                start = 0
                limit = 50
                
                while True:
                    # Build URL with pagination
                    url = urljoin(confluence_url, f"{self.api_version}/space")
                    params = {
                        'start': start,
                        'limit': limit,
                        'expand': 'description,homepage,metadata.labels'
                    }
                    
                    # Filter by space keys if provided
                    if space_keys:
                        params['spaceKey'] = ','.join(space_keys)
                    
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"Failed to get spaces: {response.status} - {error_text}")
                        
                        data = await response.json()
                        results = data.get('results', [])
                        
                        for space in results:
                            spaces.append({
                                'key': space.get('key'),
                                'name': space.get('name'),
                                'type': space.get('type'),
                                'description': space.get('description', {}).get('plain', {}).get('value', ''),
                                'homepage_id': space.get('homepage', {}).get('id'),
                                'created_date': space.get('createdDate'),
                                'labels': [label.get('name') for label in space.get('metadata', {}).get('labels', {}).get('results', [])]
                            })
                        
                        # Check if there are more results
                        if len(results) < limit:
                            break
                        start += limit
                
                logger.info(f"Retrieved {len(spaces)} Confluence spaces")
                return spaces
                
        except Exception as e:
            logger.error(f"Failed to get Confluence spaces: {str(e)}")
            raise
    
    async def get_space_pages(self, confluence_url: str, email: str, api_token: str,
                             space_key: str, project_id: str, 
                             include_attachments: bool = False) -> List[Dict[str, Any]]:
        """
        Get all pages from a Confluence space
        
        Args:
            confluence_url: Confluence instance URL
            email: User email for authentication
            api_token: API token for authentication
            space_key: Space key to retrieve pages from
            project_id: Project ID for data organization
            include_attachments: Whether to process page attachments
            
        Returns:
            List of processed page information
        """
        try:
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                auth_string = f"{email}:{api_token}"
                auth_header = base64.b64encode(auth_string.encode()).decode()
                
                headers = {
                    'Authorization': f'Basic {auth_header}',
                    'Accept': 'application/json'
                }
                
                pages = []
                start = 0
                limit = 25  # Smaller limit for pages due to content size
                
                while True:
                    # Get pages from space
                    url = urljoin(confluence_url, f"{self.content_api_version}")
                    params = {
                        'spaceKey': space_key,
                        'type': 'page',
                        'status': 'current',
                        'start': start,
                        'limit': limit,
                        'expand': 'body.storage,version,ancestors,children.page,metadata.labels,space'
                    }
                    
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Failed to get pages from space {space_key}: {response.status} - {error_text}")
                            break
                        
                        data = await response.json()
                        results = data.get('results', [])
                        
                        # Process pages in batches
                        page_batch = []
                        for page in results:
                            page_info = await self._process_page_content(
                                page, confluence_url, headers, session, project_id, include_attachments
                            )
                            if page_info:
                                page_batch.append(page_info)
                                pages.append(page_info)
                        
                        # Process batch for vector storage and knowledge graph
                        if page_batch:
                            await self._process_page_batch(page_batch, project_id)
                        
                        # Check if there are more results
                        if len(results) < limit:
                            break
                        start += limit
                
                logger.info(f"Retrieved and processed {len(pages)} pages from space {space_key}")
                return pages
                
        except Exception as e:
            logger.error(f"Failed to get pages from space {space_key}: {str(e)}")
            raise
    
    async def sync_workspace_data(self, confluence_url: str, email: str, api_token: str,
                                 project_id: str, space_keys: Optional[List[str]] = None,
                                 include_attachments: bool = False,
                                 sync_window_days: int = 7) -> Dict[str, Any]:
        """
        Synchronize Confluence workspace data for a project
        
        Args:
            confluence_url: Confluence instance URL
            email: User email for authentication
            api_token: API token for authentication
            project_id: Project ID for data organization
            space_keys: Optional list of specific spaces to sync
            include_attachments: Whether to process attachments
            sync_window_days: Days to look back for incremental sync
            
        Returns:
            Sync statistics and results
        """
        try:
            start_time = datetime.utcnow()
            total_pages = 0
            total_attachments = 0
            errors = []
            
            # Get spaces to sync
            spaces = await self.get_spaces(confluence_url, email, api_token, space_keys)
            
            logger.info(f"Starting Confluence sync for {len(spaces)} spaces")
            
            for space in spaces:
                try:
                    space_key = space['key']
                    logger.info(f"Syncing space: {space_key} ({space['name']})")
                    
                    # Create space entity in knowledge graph
                    await self.knowledge_graph.add_entity(
                        project_id=project_id,
                        entity_type="confluence_space",
                        entity_id=space_key,
                        properties={
                            'name': space['name'],
                            'type': space['type'],
                            'description': space['description'],
                            'created_date': space['created_date'],
                            'labels': space['labels']
                        }
                    )
                    
                    # Get and process pages
                    pages = await self.get_space_pages(
                        confluence_url, email, api_token, space_key, 
                        project_id, include_attachments
                    )
                    
                    total_pages += len(pages)
                    
                    # Count attachments
                    for page in pages:
                        total_attachments += len(page.get('attachments', []))
                    
                except Exception as e:
                    error_msg = f"Failed to sync space {space.get('key', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            sync_stats = {
                'status': 'completed' if not errors else 'completed_with_errors',
                'duration_seconds': int(duration),
                'spaces_processed': len(spaces),
                'pages_processed': total_pages,
                'attachments_processed': total_attachments,
                'errors': errors,
                'started_at': start_time.isoformat(),
                'completed_at': end_time.isoformat()
            }
            
            logger.info(f"Confluence sync completed: {sync_stats}")
            return sync_stats
            
        except Exception as e:
            logger.error(f"Confluence workspace sync failed: {str(e)}")
            raise
    
    async def _process_page_content(self, page: Dict[str, Any], confluence_url: str,
                                   headers: Dict[str, str], session: aiohttp.ClientSession,
                                   project_id: str, include_attachments: bool) -> Optional[Dict[str, Any]]:
        """
        Process individual page content and metadata
        
        Args:
            page: Page data from Confluence API
            confluence_url: Confluence instance URL
            headers: HTTP headers for authentication
            session: aiohttp session
            project_id: Project ID for data organization
            include_attachments: Whether to process attachments
            
        Returns:
            Processed page information or None if processing failed
        """
        try:
            page_id = page.get('id')
            title = page.get('title', '')
            
            # Extract content
            body = page.get('body', {}).get('storage', {}).get('value', '')
            
            # Clean HTML content
            clean_content = self._clean_html_content(body)
            
            # Skip if content is too large
            if len(clean_content) > self.max_page_size:
                logger.warning(f"Skipping page {page_id} - content too large ({len(clean_content)} bytes)")
                return None
            
            # Extract metadata
            version = page.get('version', {})
            space = page.get('space', {})
            ancestors = page.get('ancestors', [])
            labels = page.get('metadata', {}).get('labels', {}).get('results', [])
            
            # Build page hierarchy path
            hierarchy_path = []
            for ancestor in ancestors:
                hierarchy_path.append(ancestor.get('title', ''))
            hierarchy_path.append(title)
            
            # Get page URL
            page_url = urljoin(confluence_url, f"pages/viewpage.action?pageId={page_id}")
            
            page_info = {
                'id': page_id,
                'title': title,
                'content': clean_content,
                'url': page_url,
                'space_key': space.get('key'),
                'space_name': space.get('name'),
                'version_number': version.get('number', 1),
                'created_date': version.get('when'),
                'created_by': version.get('by', {}).get('displayName'),
                'hierarchy_path': hierarchy_path,
                'labels': [label.get('name') for label in labels],
                'content_length': len(clean_content),
                'attachments': []
            }
            
            # Process attachments if requested
            if include_attachments and clean_content:
                attachments = await self._get_page_attachments(
                    page_id, confluence_url, headers, session, project_id
                )
                page_info['attachments'] = attachments
            
            return page_info
            
        except Exception as e:
            logger.error(f"Failed to process page {page.get('id', 'unknown')}: {str(e)}")
            return None
    
    async def _get_page_attachments(self, page_id: str, confluence_url: str,
                                   headers: Dict[str, str], session: aiohttp.ClientSession,
                                   project_id: str) -> List[Dict[str, Any]]:
        """
        Get and process page attachments
        
        Args:
            page_id: Page ID to get attachments for
            confluence_url: Confluence instance URL
            headers: HTTP headers for authentication
            session: aiohttp session
            project_id: Project ID for data organization
            
        Returns:
            List of processed attachment information
        """
        try:
            attachments = []
            
            # Get attachments list
            url = urljoin(confluence_url, f"{self.content_api_version}/{page_id}/child/attachment")
            params = {'expand': 'version,metadata'}
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    logger.warning(f"Failed to get attachments for page {page_id}")
                    return attachments
                
                data = await response.json()
                results = data.get('results', [])
                
                for attachment in results:
                    try:
                        attachment_id = attachment.get('id')
                        title = attachment.get('title', '')
                        media_type = attachment.get('metadata', {}).get('mediaType', '')
                        size = attachment.get('extensions', {}).get('fileSize', 0)
                        
                        # Skip if too large or unsupported type
                        if size > self.max_attachment_size:
                            logger.warning(f"Skipping attachment {attachment_id} - too large ({size} bytes)")
                            continue
                        
                        if media_type not in self.supported_attachment_types:
                            logger.debug(f"Skipping attachment {attachment_id} - unsupported type ({media_type})")
                            continue
                        
                        # Download attachment content
                        download_url = urljoin(confluence_url, f"{self.content_api_version}/{attachment_id}/data")
                        
                        async with session.get(download_url, headers=headers) as download_response:
                            if download_response.status == 200:
                                content = await download_response.read()
                                
                                # Process attachment through file processor
                                processed_attachment = await self.file_processor.process_attachment(
                                    filename=title,
                                    content=content,
                                    media_type=media_type,
                                    project_id=project_id,
                                    source_url=download_url
                                )
                                
                                if processed_attachment:
                                    attachments.append({
                                        'id': attachment_id,
                                        'title': title,
                                        'media_type': media_type,
                                        'size': size,
                                        'processed': True,
                                        'content_preview': processed_attachment.get('content_preview', '')
                                    })
                    
                    except Exception as e:
                        logger.error(f"Failed to process attachment {attachment.get('id', 'unknown')}: {str(e)}")
                        continue
            
            return attachments
            
        except Exception as e:
            logger.error(f"Failed to get attachments for page {page_id}: {str(e)}")
            return []
    
    async def _process_page_batch(self, pages: List[Dict[str, Any]], project_id: str):
        """
        Process a batch of pages for vector storage and knowledge graph
        
        Args:
            pages: List of processed page information
            project_id: Project ID for data organization
        """
        try:
            # Prepare documents for vector storage
            documents = []
            entities = []
            relationships = []
            
            for page in pages:
                page_id = page['id']
                title = page['title']
                content = page['content']
                
                # Skip empty content
                if not content.strip():
                    continue
                
                # Score content importance
                importance_score = await self.importance_filter.score_data_importance(
                    content=content,
                    data_type="DOCUMENT",
                    project_id=project_id,
                    metadata={
                        'title': title,
                        'space_key': page['space_key'],
                        'hierarchy_path': page['hierarchy_path'],
                        'labels': page['labels'],
                        'created_by': page['created_by']
                    }
                )
                
                # Only process if importance score is above threshold
                if importance_score.importance_level.value >= 0.4:  # MEDIUM or higher
                    # Prepare for vector storage
                    documents.append({
                        'id': f"confluence_page_{page_id}",
                        'content': content,
                        'metadata': {
                            'source': 'confluence',
                            'type': 'page',
                            'title': title,
                            'url': page['url'],
                            'space_key': page['space_key'],
                            'space_name': page['space_name'],
                            'hierarchy_path': ' > '.join(page['hierarchy_path']),
                            'labels': page['labels'],
                            'created_date': page['created_date'],
                            'created_by': page['created_by'],
                            'importance_score': importance_score.score,
                            'project_id': project_id
                        }
                    })
                    
                    # Create knowledge graph entities
                    entities.append({
                        'project_id': project_id,
                        'entity_type': 'confluence_page',
                        'entity_id': page_id,
                        'properties': {
                            'title': title,
                            'space_key': page['space_key'],
                            'space_name': page['space_name'],
                            'url': page['url'],
                            'hierarchy_path': page['hierarchy_path'],
                            'labels': page['labels'],
                            'content_length': page['content_length'],
                            'version_number': page['version_number'],
                            'created_date': page['created_date'],
                            'created_by': page['created_by'],
                            'importance_score': importance_score.score
                        }
                    })
                    
                    # Create relationships
                    if page['created_by']:
                        relationships.append({
                            'project_id': project_id,
                            'source_type': 'person',
                            'source_id': page['created_by'],
                            'target_type': 'confluence_page',
                            'target_id': page_id,
                            'relationship_type': 'AUTHORED',
                            'strength': 0.9,
                            'metadata': {
                                'created_date': page['created_date'],
                                'space_key': page['space_key']
                            }
                        })
                    
                    # Create space relationships
                    relationships.append({
                        'project_id': project_id,
                        'source_type': 'confluence_space',
                        'source_id': page['space_key'],
                        'target_type': 'confluence_page',
                        'target_id': page_id,
                        'relationship_type': 'CONTAINS',
                        'strength': 1.0,
                        'metadata': {
                            'hierarchy_level': len(page['hierarchy_path'])
                        }
                    })
            
            # Store in vector database
            if documents:
                await self.vector_db.add_documents(documents)
                logger.info(f"Added {len(documents)} Confluence pages to vector database")
            
            # Store in knowledge graph
            if entities:
                await self.knowledge_graph.add_entities_batch(entities)
                logger.info(f"Added {len(entities)} Confluence page entities to knowledge graph")
            
            if relationships:
                await self.knowledge_graph.add_relationships_batch(relationships)
                logger.info(f"Added {len(relationships)} Confluence relationships to knowledge graph")
                
        except Exception as e:
            logger.error(f"Failed to process page batch: {str(e)}")
            raise
    
    def _clean_html_content(self, html_content: str) -> str:
        """
        Clean HTML content and extract plain text
        
        Args:
            html_content: Raw HTML content from Confluence
            
        Returns:
            Cleaned plain text content
        """
        try:
            # Remove HTML tags
            import re
            
            # Remove script and style elements
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags but keep content
            html_content = re.sub(r'<[^>]+>', ' ', html_content)
            
            # Decode HTML entities
            import html
            html_content = html.unescape(html_content)
            
            # Clean up whitespace
            html_content = re.sub(r'\s+', ' ', html_content)
            html_content = html_content.strip()
            
            return html_content
            
        except Exception as e:
            logger.error(f"Failed to clean HTML content: {str(e)}")
            return html_content  # Return original if cleaning fails
