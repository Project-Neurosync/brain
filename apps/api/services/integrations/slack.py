"""
Slack Integration Service for NeuroSync API
Handles Slack API authentication, channel discovery, and message ingestion
"""

import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session
from models.integration import Integration
from models.project import Project
from .base import BaseIntegrationService

# Create logger
logger = logging.getLogger(__name__)

class SlackIntegrationService(BaseIntegrationService):
    """
    Slack Integration Service
    Handles Slack API authentication, workspace information, channel discovery, and message ingestion
    """
    
    # Default API endpoints
    API_BASE = "https://slack.com/api"
    
    def __init__(self, db: Session, integration: Optional[Integration] = None):
        """
        Initialize Slack integration service
        
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
        Test Slack API connection
        
        Args:
            config: Slack integration config (token)
            
        Returns:
            Dict with connection test results
        """
        token = config.get("token")
        
        if not token:
            return {
                "success": False,
                "message": "Slack Bot Token is required"
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Test API connection by getting auth info
            endpoint = f"{self.API_BASE}/auth.test"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(endpoint, headers=headers) as response:
                result = await response.json()
                
                if result.get("ok"):
                    return {
                        "success": True,
                        "message": f"Successfully connected to Slack workspace: {result.get('team')}",
                        "details": {
                            "team": result.get("team"),
                            "team_id": result.get("team_id"),
                            "bot_id": result.get("bot_id"),
                            "user_id": result.get("user_id")
                        }
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Slack API error: {result.get('error')}",
                        "details": {"error": result.get("error")}
                    }
        except Exception as e:
            logger.error(f"Error testing Slack connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to Slack: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def get_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get Slack metadata (workspace info, channels, users)
        
        Args:
            config: Slack integration config (token)
            
        Returns:
            Dict with Slack metadata
        """
        token = config.get("token")
        
        if not token:
            return {
                "success": False,
                "message": "Slack Bot Token is required"
            }
        
        try:
            # Create session if not exists
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Get workspace info
            endpoint = f"{self.API_BASE}/team.info"
            async with self.session.get(endpoint, headers=headers) as response:
                team_result = await response.json()
                
                if not team_result.get("ok"):
                    return {
                        "success": False,
                        "message": f"Slack API error: {team_result.get('error')}",
                        "details": {"error": team_result.get("error")}
                    }
                
                team_info = team_result.get("team", {})
            
            # Get channels
            endpoint = f"{self.API_BASE}/conversations.list"
            params = {"limit": 100, "types": "public_channel,private_channel"}
            
            channels = []
            while True:
                async with self.session.get(endpoint, params=params, headers=headers) as response:
                    channels_result = await response.json()
                    
                    if not channels_result.get("ok"):
                        return {
                            "success": False,
                            "message": f"Slack API error: {channels_result.get('error')}",
                            "details": {"error": channels_result.get("error")}
                        }
                    
                    channels.extend(channels_result.get("channels", []))
                    
                    # Check if we need to paginate
                    cursor = channels_result.get("response_metadata", {}).get("next_cursor")
                    if not cursor:
                        break
                    
                    params["cursor"] = cursor
            
            # Format channel data
            formatted_channels = []
            for channel in channels:
                formatted_channels.append({
                    "id": channel.get("id"),
                    "name": channel.get("name"),
                    "is_private": channel.get("is_private", False),
                    "topic": channel.get("topic", {}).get("value", ""),
                    "purpose": channel.get("purpose", {}).get("value", ""),
                    "member_count": channel.get("num_members", 0)
                })
            
            # Get bot info
            endpoint = f"{self.API_BASE}/auth.test"
            async with self.session.post(endpoint, headers=headers) as response:
                auth_result = await response.json()
                
                if not auth_result.get("ok"):
                    bot_info = {"error": "Could not retrieve bot information"}
                else:
                    bot_info = {
                        "bot_id": auth_result.get("bot_id"),
                        "user_id": auth_result.get("user_id")
                    }
            
            return {
                "success": True,
                "workspace": {
                    "name": team_info.get("name"),
                    "id": team_info.get("id"),
                    "domain": team_info.get("domain"),
                    "icon": team_info.get("icon", {}).get("image_132")
                },
                "bot": bot_info,
                "channels": formatted_channels,
                "channel_count": len(formatted_channels)
            }
        except Exception as e:
            logger.error(f"Error getting Slack metadata: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting Slack metadata: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def ingest_data(self, config: Dict[str, Any], project_id: UUID) -> Dict[str, Any]:
        """
        Ingest data from Slack integration
        
        Args:
            config: Slack integration config (token, channels)
            project_id: UUID of the project to ingest data for
            
        Returns:
            Dict with ingestion results
        """
        token = config.get("token")
        channels = config.get("channels", [])
        
        if not token:
            return {
                "success": False,
                "message": "Slack Bot Token is required"
            }
        
        if not channels:
            return {
                "success": False,
                "message": "No Slack channels selected for ingestion"
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
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Get user information to enrich messages
            endpoint = f"{self.API_BASE}/users.list"
            params = {"limit": 200}
            
            users = []
            while True:
                async with self.session.get(endpoint, params=params, headers=headers) as response:
                    users_result = await response.json()
                    
                    if not users_result.get("ok"):
                        logger.error(f"Slack API error: {users_result.get('error')}")
                        break
                    
                    users.extend(users_result.get("members", []))
                    
                    # Check if we need to paginate
                    cursor = users_result.get("response_metadata", {}).get("next_cursor")
                    if not cursor:
                        break
                    
                    params["cursor"] = cursor
            
            # Create user lookup dictionary
            user_lookup = {}
            for user in users:
                user_lookup[user.get("id")] = {
                    "name": user.get("name"),
                    "real_name": user.get("real_name"),
                    "display_name": user.get("profile", {}).get("display_name"),
                    "title": user.get("profile", {}).get("title"),
                    "email": user.get("profile", {}).get("email"),
                    "avatar": user.get("profile", {}).get("image_72")
                }
            
            # Set up a time window for incremental sync (default: 7 days)
            sync_window = config.get("sync_window", 7)
            time_window = datetime.utcnow() - timedelta(days=sync_window)
            oldest_timestamp = time_window.timestamp()
            
            # Process each channel
            total_messages = 0
            processed_messages = 0
            skipped_messages = 0
            channel_results = []
            
            for channel in channels:
                channel_id = channel.get("id")
                
                channel_result = {
                    "channel_id": channel_id,
                    "channel_name": channel.get("name"),
                    "messages_total": 0,
                    "messages_processed": 0,
                    "messages_skipped": 0
                }
                
                try:
                    # Get messages for the channel
                    messages_data = await self._get_channel_messages(
                        token=token,
                        channel_id=channel_id,
                        oldest=oldest_timestamp,
                        headers=headers
                    )
                    
                    channel_result["messages_total"] = len(messages_data)
                    total_messages += len(messages_data)
                    
                    # Process messages in batches
                    batch_size = 20
                    for i in range(0, len(messages_data), batch_size):
                        batch = messages_data[i:i+batch_size]
                        batch_results = await self._process_messages_batch(
                            batch=batch,
                            channel=channel,
                            user_lookup=user_lookup,
                            project_id=project_id
                        )
                        
                        processed_messages += batch_results["processed"]
                        skipped_messages += batch_results["skipped"]
                        channel_result["messages_processed"] += batch_results["processed"]
                        channel_result["messages_skipped"] += batch_results["skipped"]
                    
                    channel_results.append(channel_result)
                    
                except Exception as e:
                    logger.error(f"Error processing Slack channel {channel.get('name')}: {str(e)}")
                    channel_result["error"] = str(e)
                    channel_results.append(channel_result)
            
            # Update integration sync status
            if self.integration:
                self.integration.last_sync_completed_at = datetime.utcnow()
                self.integration.sync_status = "completed"
                
                # Schedule next sync (default: 12 hours)
                next_sync_hours = config.get("next_sync_hours", 12)
                self.integration.next_sync_at = datetime.utcnow() + timedelta(hours=next_sync_hours)
                
                self.db.commit()
            
            return {
                "success": True,
                "message": f"Successfully ingested {processed_messages} messages from {len(channel_results)} Slack channels",
                "details": {
                    "channels_processed": len(channel_results),
                    "total_messages": total_messages,
                    "processed_messages": processed_messages,
                    "skipped_messages": skipped_messages,
                    "channel_results": channel_results
                }
            }
        
        except Exception as e:
            logger.error(f"Error ingesting Slack data: {str(e)}")
            
            # Update integration sync status on error
            if self.integration:
                self.integration.last_sync_completed_at = datetime.utcnow()
                self.integration.sync_status = "failed"
                self.integration.last_sync_error = str(e)
                self.db.commit()
            
            return {
                "success": False,
                "message": f"Error ingesting Slack data: {str(e)}"
            }
        finally:
            # Close session if we created it here
            if self.session and not hasattr(self, "_session_exists"):
                await self.session.close()
                self.session = None
    
    async def _get_channel_messages(self, token: str, channel_id: str, oldest: float, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Get messages for a Slack channel
        
        Args:
            token: Slack Bot Token
            channel_id: Slack channel ID
            oldest: Timestamp for oldest message to retrieve
            headers: Request headers
            
        Returns:
            List of messages
        """
        endpoint = f"{self.API_BASE}/conversations.history"
        params = {"channel": channel_id, "limit": 100, "oldest": str(oldest)}
        
        all_messages = []
        
        while True:
            async with self.session.get(endpoint, params=params, headers=headers) as response:
                result = await response.json()
                
                if not result.get("ok"):
                    error_msg = result.get("error", "Unknown error")
                    logger.error(f"Slack API error: {error_msg}")
                    raise Exception(f"Slack API error: {error_msg}")
                
                messages = result.get("messages", [])
                all_messages.extend(messages)
                
                # Check if we need to paginate
                has_more = result.get("has_more", False)
                if not has_more or not messages:
                    break
                
                # Update cursor for pagination
                params["cursor"] = result.get("response_metadata", {}).get("next_cursor")
        
        # Get thread replies for messages that have threads
        threaded_messages = [msg for msg in all_messages if msg.get("thread_ts") and msg.get("thread_ts") == msg.get("ts")]
        
        for thread_parent in threaded_messages:
            thread_ts = thread_parent.get("thread_ts")
            thread_replies = await self._get_thread_replies(token, channel_id, thread_ts, headers)
            
            # Add thread replies to the message list
            for reply in thread_replies:
                if reply.get("ts") != thread_parent.get("ts"):  # Don't add the parent message again
                    all_messages.append(reply)
        
        return all_messages
    
    async def _get_thread_replies(self, token: str, channel_id: str, thread_ts: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Get thread replies for a message
        
        Args:
            token: Slack Bot Token
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            headers: Request headers
            
        Returns:
            List of thread replies
        """
        endpoint = f"{self.API_BASE}/conversations.replies"
        params = {"channel": channel_id, "ts": thread_ts, "limit": 100}
        
        all_replies = []
        
        while True:
            async with self.session.get(endpoint, params=params, headers=headers) as response:
                result = await response.json()
                
                if not result.get("ok"):
                    error_msg = result.get("error", "Unknown error")
                    logger.error(f"Slack API error: {error_msg}")
                    return []  # Return empty list instead of raising exception
                
                replies = result.get("messages", [])
                all_replies.extend(replies)
                
                # Check if we need to paginate
                has_more = result.get("has_more", False)
                if not has_more or not replies:
                    break
                
                # Update cursor for pagination
                params["cursor"] = result.get("response_metadata", {}).get("next_cursor")
        
        return all_replies
    
    async def _process_messages_batch(self, batch: List[Dict[str, Any]], channel: Dict[str, Any], 
                                     user_lookup: Dict[str, Dict[str, Any]], project_id: UUID) -> Dict[str, int]:
        """
        Process a batch of messages
        
        Args:
            batch: List of messages to process
            channel: Channel information
            user_lookup: User lookup dictionary
            project_id: UUID of the project
            
        Returns:
            Dict with processing results
        """
        processed = 0
        skipped = 0
        
        for message in batch:
            try:
                # Skip bot messages and system messages
                if message.get("subtype") in ["bot_message", "channel_join", "channel_leave", "channel_topic", "channel_purpose"]:
                    skipped += 1
                    continue
                
                # Basic message data
                message_data = {
                    "ts": message.get("ts"),
                    "text": message.get("text", ""),
                    "user_id": message.get("user"),
                    "channel_id": channel.get("id"),
                    "channel_name": channel.get("name"),
                    "is_thread_parent": message.get("thread_ts") == message.get("ts") if message.get("thread_ts") else False,
                    "thread_ts": message.get("thread_ts"),
                    "has_attachments": len(message.get("attachments", [])) > 0,
                    "has_files": len(message.get("files", [])) > 0,
                    "timestamp": message.get("ts"),
                    "reactions": message.get("reactions", []),
                }
                
                # Add user info if available
                if message.get("user") and message.get("user") in user_lookup:
                    user_info = user_lookup.get(message.get("user"))
                    message_data["user"] = user_info
                
                # Format attachments if any
                if message.get("attachments"):
                    attachments = []
                    for attachment in message.get("attachments", []):
                        attachments.append({
                            "title": attachment.get("title"),
                            "text": attachment.get("text"),
                            "fallback": attachment.get("fallback"),
                            "author_name": attachment.get("author_name")
                        })
                    message_data["attachments"] = attachments
                
                # Apply ML importance filter (placeholder for now)
                importance_score = await self._filter_data_importance(message_data)
                message_data["importance_score"] = importance_score
                
                # Skip items with very low importance
                if importance_score < 0.2:  # Threshold for "noise"
                    skipped += 1
                    continue
                
                # Prepare data for persistence
                documents = self._prepare_documents_from_message(message_data, project_id)
                
                # Persist data to vector database
                await self._persist_data(documents, project_id)
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing Slack message: {str(e)}")
                skipped += 1
        
        return {"processed": processed, "skipped": skipped}
    
    def _prepare_documents_from_message(self, message_data: Dict[str, Any], project_id: UUID) -> List[Dict[str, Any]]:
        """
        Prepare documents from Slack message data for persistence
        
        Args:
            message_data: Message data
            project_id: UUID of the project
            
        Returns:
            List of documents for vector database
        """
        documents = []
        
        # Create document ID from channel and timestamp
        doc_id = f"slack-msg-{message_data['channel_id']}-{message_data['ts'].replace('.', '-')}"
        
        # Format user information
        user_info = message_data.get("user", {})
        user_display = user_info.get("real_name") or user_info.get("display_name") or user_info.get("name") or "Unknown User"
        
        # Create document content
        content = f"[{user_display}]: {message_data['text']}"
        
        # Add attachment content if available
        if message_data.get("attachments"):
            for attachment in message_data.get("attachments"):
                if attachment.get("text"):
                    content += f"\n\nAttachment: {attachment.get('text')}"
        
        # Create document metadata
        metadata = {
            "source": "slack",
            "source_type": "message",
            "project_id": str(project_id),
            "channel_id": message_data["channel_id"],
            "channel_name": message_data["channel_name"],
            "ts": message_data["ts"],
            "user": user_display,
            "user_id": message_data.get("user_id"),
            "is_thread": bool(message_data.get("thread_ts")),
            "is_thread_parent": message_data.get("is_thread_parent", False),
            "timestamp": message_data["ts"],
            "importance_score": message_data["importance_score"]
        }
        
        # Create document
        document = {
            "id": doc_id,
            "content": content,
            "metadata": metadata
        }
        
        documents.append(document)
        
        return documents
    
    async def _filter_data_importance(self, data: Dict[str, Any]) -> float:
        """
        Filter data by importance (placeholder for ML model)
        
        Args:
            data: Data to filter
            
        Returns:
            Importance score (0.0 to 1.0)
        """
        # Simple heuristic scoring based on content length, reactions, etc.
        # This will be replaced with a proper ML model in the future
        
        # Start with a base score
        score = 0.5
        
        # Adjust based on content length
        message_length = len(data.get("text", ""))
        if message_length > 500:
            score += 0.2
        elif message_length > 200:
            score += 0.1
        elif message_length < 20:
            score -= 0.1
        
        # Adjust based on thread status (threads tend to be more important)
        if data.get("is_thread_parent"):
            score += 0.15
        
        # Adjust based on reactions (more reactions = more important)
        reaction_count = len(data.get("reactions", []))
        if reaction_count > 3:
            score += 0.2
        elif reaction_count > 0:
            score += 0.1
        
        # Adjust based on attachments or files
        if data.get("has_attachments") or data.get("has_files"):
            score += 0.1
        
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
