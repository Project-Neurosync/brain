"""
NeuroSync AI Backend - Data Ingestion Service
Handles processing and ingestion of data from various sources (GitHub, Jira, Slack, etc.)
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

from ..models.requests import DataIngestionRequest
from ..models.responses import DataIngestionResponse
from .vector_service import VectorService
from .ai_service import AIService

logger = logging.getLogger(__name__)

class DataIngestionService:
    """Service for processing and ingesting data from various sources"""
    
    def __init__(self, vector_service: VectorService, ai_service: AIService):
        self.vector_service = vector_service
        self.ai_service = ai_service
        
    async def process_ingestion(self, request: DataIngestionRequest) -> DataIngestionResponse:
        """Process data ingestion request"""
        start_time = datetime.utcnow()
        ingestion_id = self._generate_ingestion_id(request)
        
        try:
            # Route to appropriate processor based on source type
            processor_map = {
                "github": self._process_github_data,
                "jira": self._process_jira_data,
                "slack": self._process_slack_data,
                "meeting": self._process_meeting_data,
                "document": self._process_document_data,
                "confluence": self._process_confluence_data,
                "notion": self._process_notion_data
            }
            
            processor = processor_map.get(request.source_type)
            if not processor:
                return DataIngestionResponse(
                    success=False,
                    message=f"Unsupported source type: {request.source_type}",
                    ingestion_id=ingestion_id,
                    items_processed=0,
                    items_failed=1,
                    processing_time=0.0
                )
            
            # Process the data
            documents = await processor(request.data, request.project_id, request.metadata)
            
            # Add documents to vector store
            if documents:
                vector_result = await self.vector_service.add_documents(
                    request.project_id, 
                    documents
                )
                
                items_processed = vector_result.get("documents_added", 0)
                items_failed = len(documents) - items_processed
            else:
                items_processed = 0
                items_failed = 1
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return DataIngestionResponse(
                success=items_processed > 0,
                message=f"Processed {items_processed} items from {request.source_type}",
                ingestion_id=ingestion_id,
                items_processed=items_processed,
                items_failed=items_failed,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing ingestion: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return DataIngestionResponse(
                success=False,
                message=f"Ingestion failed: {str(e)}",
                ingestion_id=ingestion_id,
                items_processed=0,
                items_failed=1,
                processing_time=processing_time
            )
    
    async def _process_github_data(
        self, 
        data: Dict[str, Any], 
        project_id: str, 
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process GitHub repository data"""
        documents = []
        
        # Process repository files
        if "files" in data:
            for file_data in data["files"]:
                if self._should_process_file(file_data.get("path", "")):
                    doc = await self._create_code_document(file_data, project_id, metadata)
                    if doc:
                        documents.append(doc)
        
        # Process commits
        if "commits" in data:
            for commit in data["commits"]:
                doc = await self._create_commit_document(commit, project_id, metadata)
                if doc:
                    documents.append(doc)
        
        # Process issues
        if "issues" in data:
            for issue in data["issues"]:
                doc = await self._create_issue_document(issue, project_id, metadata)
                if doc:
                    documents.append(doc)
        
        # Process pull requests
        if "pull_requests" in data:
            for pr in data["pull_requests"]:
                doc = await self._create_pr_document(pr, project_id, metadata)
                if doc:
                    documents.append(doc)
        
        # Process README and documentation
        if "readme" in data:
            doc = await self._create_readme_document(data["readme"], project_id, metadata)
            if doc:
                documents.append(doc)
        
        logger.info(f"Processed {len(documents)} GitHub documents")
        return documents
    
    async def _process_jira_data(
        self, 
        data: Dict[str, Any], 
        project_id: str, 
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process Jira project data"""
        documents = []
        
        # Process issues/tickets
        if "issues" in data:
            for issue in data["issues"]:
                doc = await self._create_jira_issue_document(issue, project_id, metadata)
                if doc:
                    documents.append(doc)
        
        # Process epics
        if "epics" in data:
            for epic in data["epics"]:
                doc = await self._create_jira_epic_document(epic, project_id, metadata)
                if doc:
                    documents.append(doc)
        
        # Process sprints
        if "sprints" in data:
            for sprint in data["sprints"]:
                doc = await self._create_sprint_document(sprint, project_id, metadata)
                if doc:
                    documents.append(doc)
        
        logger.info(f"Processed {len(documents)} Jira documents")
        return documents
    
    async def _process_slack_data(
        self, 
        data: Dict[str, Any], 
        project_id: str, 
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process Slack conversation data"""
        documents = []
        
        # Process channels
        if "channels" in data:
            for channel in data["channels"]:
                if "messages" in channel:
                    # Group messages into conversation threads
                    conversations = self._group_slack_messages(channel["messages"])
                    for conversation in conversations:
                        doc = await self._create_slack_conversation_document(
                            conversation, channel, project_id, metadata
                        )
                        if doc:
                            documents.append(doc)
        
        # Process direct messages
        if "direct_messages" in data:
            for dm in data["direct_messages"]:
                doc = await self._create_slack_dm_document(dm, project_id, metadata)
                if doc:
                    documents.append(doc)
        
        logger.info(f"Processed {len(documents)} Slack documents")
        return documents
    
    async def _process_meeting_data(
        self, 
        data: Dict[str, Any], 
        project_id: str, 
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process meeting transcript data"""
        documents = []
        
        # Process transcript
        if "transcript" in data:
            doc = await self._create_meeting_document(data, project_id, metadata)
            if doc:
                documents.append(doc)
        
        # Extract action items and key decisions
        if "transcript" in data:
            action_items_doc = await self._extract_action_items(data, project_id, metadata)
            if action_items_doc:
                documents.append(action_items_doc)
        
        logger.info(f"Processed {len(documents)} meeting documents")
        return documents
    
    async def _process_document_data(
        self, 
        data: Dict[str, Any], 
        project_id: str, 
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process general document data"""
        documents = []
        
        doc = {
            "id": data.get("id", self._generate_document_id(data)),
            "title": data.get("title", "Untitled Document"),
            "content": data.get("content", ""),
            "source_type": "document",
            "file_path": data.get("file_path", ""),
            "created_at": data.get("created_at", datetime.utcnow().isoformat()),
            "metadata": {
                "document_type": data.get("document_type", "general"),
                "tags": data.get("tags", []),
                "author": data.get("author", ""),
                **metadata
            }
        }
        
        # Generate summary if content is long
        if len(doc["content"]) > 1000:
            summary = await self.ai_service.generate_summary(doc["content"], "document")
            doc["metadata"]["summary"] = summary
        
        documents.append(doc)
        
        logger.info(f"Processed document: {doc['title']}")
        return documents
    
    async def _process_confluence_data(
        self, 
        data: Dict[str, Any], 
        project_id: str, 
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process Confluence page data"""
        documents = []
        
        if "pages" in data:
            for page in data["pages"]:
                doc = await self._create_confluence_document(page, project_id, metadata)
                if doc:
                    documents.append(doc)
        
        logger.info(f"Processed {len(documents)} Confluence documents")
        return documents
    
    async def _process_notion_data(
        self, 
        data: Dict[str, Any], 
        project_id: str, 
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process Notion page data"""
        documents = []
        
        if "pages" in data:
            for page in data["pages"]:
                doc = await self._create_notion_document(page, project_id, metadata)
                if doc:
                    documents.append(doc)
        
        logger.info(f"Processed {len(documents)} Notion documents")
        return documents
    
    async def _create_code_document(
        self, 
        file_data: Dict[str, Any], 
        project_id: str, 
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a document from code file data"""
        try:
            content = file_data.get("content", "")
            file_path = file_data.get("path", "")
            
            # Analyze code context
            analysis = await self.ai_service.analyze_code_context(content, file_path)
            
            doc = {
                "id": self._generate_file_id(file_path, content),
                "title": f"Code: {file_path}",
                "content": content,
                "source_type": "github",
                "file_path": file_path,
                "created_at": file_data.get("last_modified", datetime.utcnow().isoformat()),
                "metadata": {
                    "file_type": self._get_file_type(file_path),
                    "file_size": len(content),
                    "language": self._detect_language(file_path),
                    "analysis": analysis.get("analysis", ""),
                    **metadata
                }
            }
            
            return doc
            
        except Exception as e:
            logger.error(f"Error creating code document: {str(e)}")
            return None
    
    async def _create_commit_document(
        self, 
        commit: Dict[str, Any], 
        project_id: str, 
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a document from commit data"""
        try:
            commit_message = commit.get("message", "")
            commit_hash = commit.get("hash", "")
            
            content = f"Commit: {commit_hash}\n"
            content += f"Message: {commit_message}\n"
            content += f"Author: {commit.get('author', '')}\n"
            content += f"Date: {commit.get('date', '')}\n"
            
            if "files_changed" in commit:
                content += f"Files changed: {', '.join(commit['files_changed'])}\n"
            
            if "diff" in commit:
                content += f"Changes:\n{commit['diff']}"
            
            doc = {
                "id": f"commit_{commit_hash}",
                "title": f"Commit: {commit_message[:50]}...",
                "content": content,
                "source_type": "github",
                "file_path": "",
                "created_at": commit.get("date", datetime.utcnow().isoformat()),
                "metadata": {
                    "commit_hash": commit_hash,
                    "author": commit.get("author", ""),
                    "files_changed": commit.get("files_changed", []),
                    **metadata
                }
            }
            
            return doc
            
        except Exception as e:
            logger.error(f"Error creating commit document: {str(e)}")
            return None
    
    async def _create_meeting_document(
        self, 
        data: Dict[str, Any], 
        project_id: str, 
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a document from meeting data"""
        try:
            transcript = data.get("transcript", "")
            title = data.get("title", "Meeting")
            
            # Generate summary and extract key points
            summary = await self.ai_service.generate_summary(transcript, "meeting transcript")
            
            content = f"Meeting: {title}\n"
            content += f"Date: {data.get('date', '')}\n"
            content += f"Participants: {', '.join(data.get('participants', []))}\n"
            content += f"Summary: {summary}\n\n"
            content += f"Full Transcript:\n{transcript}"
            
            doc = {
                "id": data.get("id", self._generate_document_id(data)),
                "title": title,
                "content": content,
                "source_type": "meeting",
                "file_path": "",
                "created_at": data.get("date", datetime.utcnow().isoformat()),
                "metadata": {
                    "participants": data.get("participants", []),
                    "duration": data.get("duration", 0),
                    "summary": summary,
                    **metadata
                }
            }
            
            return doc
            
        except Exception as e:
            logger.error(f"Error creating meeting document: {str(e)}")
            return None
    
    def _should_process_file(self, file_path: str) -> bool:
        """Determine if a file should be processed based on its path and type"""
        # Skip binary files and common non-code files
        skip_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.exe', '.dll', '.so', '.dylib',
            '.mp3', '.mp4', '.avi', '.mov', '.wav'
        }
        
        # Skip common directories
        skip_dirs = {
            'node_modules', '.git', '.svn', '.hg', 'vendor', 'build', 'dist',
            '__pycache__', '.pytest_cache', '.coverage', 'coverage',
            'logs', 'tmp', 'temp'
        }
        
        # Check file extension
        file_ext = '.' + file_path.split('.')[-1].lower() if '.' in file_path else ''
        if file_ext in skip_extensions:
            return False
        
        # Check directory names
        path_parts = file_path.split('/')
        if any(part in skip_dirs for part in path_parts):
            return False
        
        # Skip very large files (>1MB of text is probably not useful)
        # This would need to be checked at the file level, not here
        
        return True
    
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type from path"""
        if '.' not in file_path:
            return 'unknown'
        
        ext = file_path.split('.')[-1].lower()
        
        type_map = {
            'py': 'python', 'js': 'javascript', 'ts': 'typescript',
            'java': 'java', 'cpp': 'cpp', 'c': 'c', 'h': 'header',
            'css': 'css', 'html': 'html', 'xml': 'xml',
            'json': 'json', 'yaml': 'yaml', 'yml': 'yaml',
            'md': 'markdown', 'txt': 'text', 'rst': 'restructuredtext',
            'sql': 'sql', 'sh': 'shell', 'bash': 'shell',
            'dockerfile': 'docker', 'makefile': 'makefile'
        }
        
        return type_map.get(ext, ext)
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path"""
        return self._get_file_type(file_path)
    
    def _generate_ingestion_id(self, request: DataIngestionRequest) -> str:
        """Generate a unique ingestion ID"""
        content = f"{request.source_type}_{request.project_id}_{datetime.utcnow().isoformat()}"
        return f"ing_{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def _generate_document_id(self, data: Dict[str, Any]) -> str:
        """Generate a unique document ID"""
        content = json.dumps(data, sort_keys=True, default=str)
        return f"doc_{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def _generate_file_id(self, file_path: str, content: str) -> str:
        """Generate a unique file ID based on path and content hash"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"file_{path_hash}_{content_hash}"
    
    def _group_slack_messages(self, messages: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group Slack messages into conversation threads"""
        # Simple grouping by time gaps and thread references
        conversations = []
        current_conversation = []
        last_timestamp = None
        
        for message in sorted(messages, key=lambda x: x.get('timestamp', 0)):
            timestamp = message.get('timestamp', 0)
            
            # Start new conversation if gap > 30 minutes or explicit thread
            if (last_timestamp and timestamp - last_timestamp > 1800) or \
               (current_conversation and message.get('thread_ts') != current_conversation[0].get('thread_ts')):
                if current_conversation:
                    conversations.append(current_conversation)
                current_conversation = [message]
            else:
                current_conversation.append(message)
            
            last_timestamp = timestamp
        
        if current_conversation:
            conversations.append(current_conversation)
        
        return conversations
    
    async def _create_slack_conversation_document(
        self, 
        messages: List[Dict[str, Any]], 
        channel: Dict[str, Any], 
        project_id: str, 
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a document from Slack conversation"""
        try:
            if not messages:
                return None
            
            channel_name = channel.get('name', 'unknown')
            first_message = messages[0]
            
            content = f"Slack Conversation in #{channel_name}\n"
            content += f"Started: {first_message.get('timestamp', '')}\n\n"
            
            for message in messages:
                user = message.get('user', 'Unknown')
                text = message.get('text', '')
                timestamp = message.get('timestamp', '')
                content += f"[{timestamp}] {user}: {text}\n"
            
            # Generate summary for longer conversations
            summary = ""
            if len(messages) > 5:
                summary = await self.ai_service.generate_summary(content, "conversation")
            
            doc = {
                "id": f"slack_{channel_name}_{first_message.get('timestamp', '')}",
                "title": f"Slack: #{channel_name} conversation",
                "content": content,
                "source_type": "slack",
                "file_path": "",
                "created_at": first_message.get('timestamp', datetime.utcnow().isoformat()),
                "metadata": {
                    "channel": channel_name,
                    "message_count": len(messages),
                    "participants": list(set(msg.get('user', '') for msg in messages)),
                    "summary": summary,
                    **metadata
                }
            }
            
            return doc
            
        except Exception as e:
            logger.error(f"Error creating Slack conversation document: {str(e)}")
            return None
