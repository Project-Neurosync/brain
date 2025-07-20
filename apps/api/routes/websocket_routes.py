"""
WebSocket API Routes for NeuroSync
Handles real-time communication endpoints and WebSocket connections
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ..core.websocket_manager import websocket_manager, WebSocketMessage, MessageType, NotificationLevel
from ..core.live_notifications import LiveNotificationService, NotificationType, NotificationPriority, NotificationChannel
from ..core.collaborative_features import CollaborativeFeaturesService
from ..core.auth_manager import AuthManager
import uuid
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Request Models for WebSocket API
class SendNotificationRequest(BaseModel):
    notification_type: str
    title: str
    message: str
    level: str = "info"
    priority: str = "normal"
    recipient_id: str
    project_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    channels: List[str] = ["websocket", "in_app"]
    action_url: Optional[str] = None
    expires_at: Optional[str] = None

class UpdateCursorRequest(BaseModel):
    project_id: str
    file_path: str
    line: int
    column: int

class UpdateSelectionRequest(BaseModel):
    project_id: str
    file_path: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    selected_text: str

class ShareAIQueryRequest(BaseModel):
    project_id: str
    query: str
    context: Dict[str, Any]
    response: Optional[str] = None

class ShareInsightRequest(BaseModel):
    project_id: str
    title: str
    content: str
    insight_type: str
    context: Dict[str, Any]
    tags: Optional[List[str]] = None

class AddCommentRequest(BaseModel):
    project_id: str
    content: str
    context: Dict[str, Any]

class ReplyToCommentRequest(BaseModel):
    project_id: str
    content: str

class ReactToInsightRequest(BaseModel):
    reaction: str

# Initialize services
notification_service = LiveNotificationService(websocket_manager)
collaboration_service = CollaborativeFeaturesService(websocket_manager, notification_service)
auth_manager = AuthManager()

router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])

@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket, 
                           token: str = Query(...),
                           project_id: Optional[str] = Query(None)):
    """
    WebSocket connection endpoint for real-time communication
    
    Args:
        websocket: WebSocket connection
        token: JWT authentication token
        project_id: Optional project to join immediately
    """
    connection_id = None
    user_id = None
    
    try:
        # Authenticate user
        try:
            user_data = auth_manager.verify_access_token(token)
            user_id = user_data.get("sub")
            
            if not user_id:
                await websocket.close(code=4001, reason="Invalid token")
                return
                
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {str(e)}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Connect user to WebSocket system
        connection_id = await websocket_manager.connect_user(
            websocket=websocket,
            user_id=user_id,
            project_id=project_id,
            user_info={"connected_at": datetime.utcnow().isoformat()}
        )
        
        # Start collaboration session if project specified
        if project_id:
            await collaboration_service.start_collaboration_session(project_id, user_id)
        
        logger.info(f"WebSocket connected: user={user_id}, connection={connection_id}, project={project_id}")
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle the message
                await websocket_manager.handle_message(connection_id, message_data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from {connection_id}")
                await websocket_manager._send_error(connection_id, "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
                await websocket_manager._send_error(connection_id, f"Message handling error: {str(e)}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    
    finally:
        # Clean up connection
        if connection_id:
            await websocket_manager.disconnect_user(connection_id)

@router.post("/notifications/send")
async def send_notification(request: SendNotificationRequest, 
                          current_user: dict = Depends(auth_manager.get_current_user)):
    """Send a notification to a user"""
    try:
        from ..core.live_notifications import Notification
        
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            notification_type=NotificationType(request.notification_type),
            title=request.title,
            message=request.message,
            level=NotificationLevel(request.level),
            priority=NotificationPriority(request.priority),
            recipient_id=request.recipient_id,
            project_id=request.project_id,
            created_at=datetime.utcnow(),
            data=request.data or {},
            metadata=request.metadata or {},
            channels=[NotificationChannel(c) for c in request.channels],
            action_url=request.action_url,
            expires_at=datetime.fromisoformat(request.expires_at) if request.expires_at else None
        )
        
        success = await notification_service.send_notification(notification)
        
        return JSONResponse({
            "success": success,
            "notification_id": notification.notification_id,
            "message": "Notification sent successfully" if success else "Failed to send notification"
        })
        
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications")
async def get_user_notifications(unread_only: bool = False,
                               limit: int = 50,
                               current_user: dict = Depends(auth_manager.get_current_user)):
    """Get notifications for the current user"""
    try:
        user_id = current_user["sub"]
        notifications = await notification_service.get_user_notifications(
            user_id, unread_only=unread_only, limit=limit
        )
        
        # Convert to response format
        notification_data = []
        for notification in notifications:
            notification_dict = {
                "notification_id": notification.notification_id,
                "notification_type": notification.notification_type.value,
                "title": notification.title,
                "message": notification.message,
                "level": notification.level.value,
                "priority": notification.priority.value,
                "project_id": notification.project_id,
                "created_at": notification.created_at.isoformat(),
                "data": notification.data,
                "read": notification.read,
                "read_at": notification.read_at.isoformat() if notification.read_at else None,
                "action_url": notification.action_url
            }
            notification_data.append(notification_dict)
        
        return JSONResponse({
            "notifications": notification_data,
            "total": len(notification_data),
            "unread_count": len([n for n in notifications if not n.read])
        })
        
    except Exception as e:
        logger.error(f"Failed to get notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str,
                               current_user: dict = Depends(auth_manager.get_current_user)):
    """Mark a notification as read"""
    try:
        user_id = current_user["sub"]
        success = await notification_service.mark_notification_read(notification_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return JSONResponse({"success": True, "message": "Notification marked as read"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/read-all")
async def mark_all_notifications_read(current_user: dict = Depends(auth_manager.get_current_user)):
    """Mark all notifications as read for the current user"""
    try:
        user_id = current_user["sub"]
        marked_count = await notification_service.mark_all_notifications_read(user_id)
        
        return JSONResponse({
            "success": True,
            "marked_count": marked_count,
            "message": f"Marked {marked_count} notifications as read"
        })
        
    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaboration/cursor")
async def update_cursor_position(request: UpdateCursorRequest,
                               current_user: dict = Depends(auth_manager.get_current_user)):
    """Update user's cursor position for collaboration"""
    try:
        user_id = current_user["sub"]
        
        await collaboration_service.update_cursor_position(
            user_id=user_id,
            project_id=request.project_id,
            file_path=request.file_path,
            line=request.line,
            column=request.column
        )
        
        return JSONResponse({"success": True, "message": "Cursor position updated"})
        
    except Exception as e:
        logger.error(f"Failed to update cursor position: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaboration/selection")
async def update_text_selection(request: UpdateSelectionRequest,
                              current_user: dict = Depends(auth_manager.get_current_user)):
    """Update user's text selection for collaboration"""
    try:
        user_id = current_user["sub"]
        
        await collaboration_service.update_text_selection(
            user_id=user_id,
            project_id=request.project_id,
            file_path=request.file_path,
            start_line=request.start_line,
            start_column=request.start_column,
            end_line=request.end_line,
            end_column=request.end_column,
            selected_text=request.selected_text
        )
        
        return JSONResponse({"success": True, "message": "Text selection updated"})
        
    except Exception as e:
        logger.error(f"Failed to update text selection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaboration/share-ai-query")
async def share_ai_query(request: ShareAIQueryRequest,
                        current_user: dict = Depends(auth_manager.get_current_user)):
    """Share an AI query with team members"""
    try:
        user_id = current_user["sub"]
        
        session_id = await collaboration_service.share_ai_query(
            user_id=user_id,
            project_id=request.project_id,
            query=request.query,
            context=request.context,
            response=request.response
        )
        
        if not session_id:
            raise HTTPException(status_code=500, detail="Failed to share AI query")
        
        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "message": "AI query shared with team"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share AI query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaboration/share-insight")
async def share_insight(request: ShareInsightRequest,
                       current_user: dict = Depends(auth_manager.get_current_user)):
    """Share an insight with the team"""
    try:
        user_id = current_user["sub"]
        
        insight_id = await collaboration_service.share_insight(
            user_id=user_id,
            project_id=request.project_id,
            title=request.title,
            content=request.content,
            insight_type=request.insight_type,
            context=request.context,
            tags=request.tags
        )
        
        if not insight_id:
            raise HTTPException(status_code=500, detail="Failed to share insight")
        
        return JSONResponse({
            "success": True,
            "insight_id": insight_id,
            "message": "Insight shared with team"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share insight: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaboration/comments")
async def add_comment(request: AddCommentRequest,
                     current_user: dict = Depends(auth_manager.get_current_user)):
    """Add a collaborative comment"""
    try:
        user_id = current_user["sub"]
        
        comment_id = await collaboration_service.add_comment(
            author_id=user_id,
            project_id=request.project_id,
            content=request.content,
            context=request.context
        )
        
        if not comment_id:
            raise HTTPException(status_code=500, detail="Failed to add comment")
        
        return JSONResponse({
            "success": True,
            "comment_id": comment_id,
            "message": "Comment added successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add comment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaboration/comments/{comment_id}/reply")
async def reply_to_comment(comment_id: str,
                          request: ReplyToCommentRequest,
                          current_user: dict = Depends(auth_manager.get_current_user)):
    """Reply to a collaborative comment"""
    try:
        user_id = current_user["sub"]
        
        reply_id = await collaboration_service.reply_to_comment(
            author_id=user_id,
            project_id=request.project_id,
            parent_comment_id=comment_id,
            content=request.content
        )
        
        if not reply_id:
            raise HTTPException(status_code=500, detail="Failed to reply to comment")
        
        return JSONResponse({
            "success": True,
            "reply_id": reply_id,
            "message": "Reply added successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reply to comment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaboration/insights/{insight_id}/react")
async def react_to_insight(insight_id: str,
                          request: ReactToInsightRequest,
                          current_user: dict = Depends(auth_manager.get_current_user)):
    """Add a reaction to a shared insight"""
    try:
        user_id = current_user["sub"]
        
        success = await collaboration_service.react_to_insight(
            user_id=user_id,
            insight_id=insight_id,
            reaction=request.reaction
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        return JSONResponse({
            "success": True,
            "message": "Reaction added successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to react to insight: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collaboration/projects/{project_id}/state")
async def get_project_collaboration_state(project_id: str,
                                        current_user: dict = Depends(auth_manager.get_current_user)):
    """Get current collaboration state for a project"""
    try:
        # TODO: Add project access validation
        
        state = await collaboration_service.get_project_collaboration_state(project_id)
        
        return JSONResponse({
            "success": True,
            "collaboration_state": state
        })
        
    except Exception as e:
        logger.error(f"Failed to get collaboration state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collaboration/files/{file_path:path}/collaborators")
async def get_file_collaborators(file_path: str,
                               current_user: dict = Depends(auth_manager.get_current_user)):
    """Get users currently collaborating on a file"""
    try:
        collaborators = await collaboration_service.get_file_collaborators(file_path)
        
        return JSONResponse({
            "success": True,
            "file_path": file_path,
            "collaborators": collaborators,
            "count": len(collaborators)
        })
        
    except Exception as e:
        logger.error(f"Failed to get file collaborators: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presence/projects/{project_id}")
async def get_project_presence(project_id: str,
                             current_user: dict = Depends(auth_manager.get_current_user)):
    """Get presence information for a project"""
    try:
        # TODO: Add project access validation
        
        presence = await websocket_manager.get_project_presence(project_id)
        
        return JSONResponse({
            "success": True,
            "project_id": project_id,
            "presence": presence
        })
        
    except Exception as e:
        logger.error(f"Failed to get project presence: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_websocket_stats(current_user: dict = Depends(auth_manager.get_current_user)):
    """Get WebSocket connection statistics"""
    try:
        # TODO: Add admin role check
        
        stats = await websocket_manager.get_connection_stats()
        
        return JSONResponse({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get WebSocket stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Notification event handlers for integration with other services
async def handle_sync_started(project_id: str, integration: str, user_id: str):
    """Handle sync started event"""
    await notification_service.notify_sync_started(project_id, integration, user_id)

async def handle_sync_completed(project_id: str, integration: str, user_id: str, 
                              items_processed: int, duration: float):
    """Handle sync completed event"""
    await notification_service.notify_sync_completed(
        project_id, integration, user_id, items_processed, duration
    )

async def handle_sync_failed(project_id: str, integration: str, user_id: str, error: str):
    """Handle sync failed event"""
    await notification_service.notify_sync_failed(project_id, integration, user_id, error)

# Export event handlers for use by other services
websocket_event_handlers = {
    'sync_started': handle_sync_started,
    'sync_completed': handle_sync_completed,
    'sync_failed': handle_sync_failed
}
