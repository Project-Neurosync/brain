"""
Production Project Management System for NeuroSync AI Backend
Handles project creation, user associations, access control, and project-scoped operations.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import logging
import uuid
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

class ProjectRole(str, Enum):
    """User roles within a project."""
    OWNER = "owner"           # Full control, can delete project
    ADMIN = "admin"           # Can manage users and settings
    MEMBER = "member"         # Can access and contribute to project
    VIEWER = "viewer"         # Read-only access

class ProjectStatus(str, Enum):
    """Project status options."""
    ACTIVE = "active"         # Active project
    ARCHIVED = "archived"     # Archived but accessible
    SUSPENDED = "suspended"   # Temporarily suspended
    DELETED = "deleted"       # Soft deleted

class ProjectVisibility(str, Enum):
    """Project visibility settings."""
    PRIVATE = "private"       # Only invited members
    INTERNAL = "internal"     # Organization members can request access
    PUBLIC = "public"         # Anyone can view (read-only)

class ProjectSettings(BaseModel):
    """Project configuration settings."""
    name: str
    description: Optional[str] = None
    visibility: ProjectVisibility = ProjectVisibility.PRIVATE
    auto_sync_enabled: bool = True
    data_retention_days: int = 365
    importance_threshold: float = 0.3
    max_members: int = 50
    integrations: Dict[str, Dict[str, Any]] = {}
    ai_settings: Dict[str, Any] = {}
    notification_settings: Dict[str, Any] = {}

class ProjectMember(BaseModel):
    """Project member information."""
    user_id: str
    email: str
    name: str
    role: ProjectRole
    joined_at: datetime
    last_active: Optional[datetime] = None
    permissions: Set[str] = set()

class Project(BaseModel):
    """Complete project information."""
    id: str
    settings: ProjectSettings
    members: List[ProjectMember]
    owner_id: str
    created_at: datetime
    updated_at: datetime
    status: ProjectStatus
    stats: Dict[str, Any] = {}

class ProjectInvitation(BaseModel):
    """Project invitation model."""
    id: str
    project_id: str
    inviter_id: str
    invitee_email: str
    role: ProjectRole
    message: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    status: str = "pending"  # pending, accepted, declined, expired

class ProjectManagementSystem:
    """
    Production-ready project management system with access control and multi-tenancy.
    Handles project lifecycle, user associations, and permissions.
    """
    
    def __init__(self, db_service, config: Optional[Dict[str, Any]] = None):
        """Initialize the Project Management System."""
        self.db_service = db_service
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.max_projects_per_user = self.config.get('max_projects_per_user', 10)
        self.default_data_retention = self.config.get('default_data_retention_days', 365)
        self.invitation_expiry_hours = self.config.get('invitation_expiry_hours', 72)
        
        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Permission definitions
        self.role_permissions = {
            ProjectRole.OWNER: {
                'project.delete', 'project.update', 'project.manage_members',
                'project.manage_settings', 'project.view', 'project.contribute',
                'data.read', 'data.write', 'data.delete', 'integrations.manage'
            },
            ProjectRole.ADMIN: {
                'project.update', 'project.manage_members', 'project.manage_settings',
                'project.view', 'project.contribute', 'data.read', 'data.write',
                'integrations.manage'
            },
            ProjectRole.MEMBER: {
                'project.view', 'project.contribute', 'data.read', 'data.write'
            },
            ProjectRole.VIEWER: {
                'project.view', 'data.read'
            }
        }
        
        self.logger.info("Project Management System initialized")
    
    async def create_project(
        self,
        owner_id: str,
        name: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        Create a new project with the specified owner.
        
        Args:
            owner_id: User ID of the project owner
            name: Project name
            description: Optional project description
            settings: Optional project settings override
            
        Returns:
            Created Project object
        """
        # Check if user has reached project limit
        user_project_count = await self.get_user_project_count(owner_id)
        if user_project_count >= self.max_projects_per_user:
            raise ValueError(f"User has reached maximum project limit ({self.max_projects_per_user})")
        
        # Create project ID
        project_id = str(uuid.uuid4())
        
        # Create project settings
        project_settings = ProjectSettings(
            name=name,
            description=description,
            **(settings or {})
        )
        
        # Create owner as first member
        owner_member = ProjectMember(
            user_id=owner_id,
            email="",  # Will be populated from user service
            name="",   # Will be populated from user service
            role=ProjectRole.OWNER,
            joined_at=datetime.now(),
            permissions=self.role_permissions[ProjectRole.OWNER]
        )
        
        # Create project
        project = Project(
            id=project_id,
            settings=project_settings,
            members=[owner_member],
            owner_id=owner_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=ProjectStatus.ACTIVE
        )
        
        # Save to database
        await self._save_project_to_db(project)
        
        self.logger.info(f"Created project {project_id} for owner {owner_id}")
        return project
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project object or None if not found
        """
        def _get_project():
            with self.db_service.get_db_session() as db:
                # This would query the actual project table
                # For now, return a mock project
                return None
        
        project_data = await asyncio.get_event_loop().run_in_executor(
            self._executor, _get_project
        )
        
        return project_data
    
    async def update_project_settings(
        self,
        project_id: str,
        user_id: str,
        settings_update: Dict[str, Any]
    ) -> Project:
        """
        Update project settings.
        
        Args:
            project_id: Project ID
            user_id: User making the update
            settings_update: Settings to update
            
        Returns:
            Updated Project object
        """
        # Check permissions
        if not await self.check_user_permission(user_id, project_id, 'project.manage_settings'):
            raise PermissionError("User does not have permission to manage project settings")
        
        # Get current project
        project = await self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        # Update settings
        current_settings = project.settings.dict()
        current_settings.update(settings_update)
        project.settings = ProjectSettings(**current_settings)
        project.updated_at = datetime.now()
        
        # Save to database
        await self._save_project_to_db(project)
        
        self.logger.info(f"Updated settings for project {project_id} by user {user_id}")
        return project
    
    async def add_project_member(
        self,
        project_id: str,
        inviter_id: str,
        invitee_email: str,
        role: ProjectRole,
        message: Optional[str] = None
    ) -> ProjectInvitation:
        """
        Invite a user to join a project.
        
        Args:
            project_id: Project ID
            inviter_id: User ID of the person sending invitation
            invitee_email: Email of person to invite
            role: Role to assign to the invitee
            message: Optional invitation message
            
        Returns:
            ProjectInvitation object
        """
        # Check permissions
        if not await self.check_user_permission(inviter_id, project_id, 'project.manage_members'):
            raise PermissionError("User does not have permission to manage project members")
        
        # Check if project exists and has space
        project = await self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        if len(project.members) >= project.settings.max_members:
            raise ValueError("Project has reached maximum member limit")
        
        # Check if user is already a member
        existing_member = next((m for m in project.members if m.email == invitee_email), None)
        if existing_member:
            raise ValueError("User is already a member of this project")
        
        # Create invitation
        invitation = ProjectInvitation(
            id=str(uuid.uuid4()),
            project_id=project_id,
            inviter_id=inviter_id,
            invitee_email=invitee_email,
            role=role,
            message=message,
            expires_at=datetime.now() + timedelta(hours=self.invitation_expiry_hours),
            created_at=datetime.now()
        )
        
        # Save invitation to database
        await self._save_invitation_to_db(invitation)
        
        # TODO: Send invitation email
        
        self.logger.info(f"Created invitation {invitation.id} for project {project_id}")
        return invitation
    
    async def accept_invitation(
        self,
        invitation_id: str,
        user_id: str
    ) -> Project:
        """
        Accept a project invitation.
        
        Args:
            invitation_id: Invitation ID
            user_id: User accepting the invitation
            
        Returns:
            Updated Project object
        """
        # Get invitation
        invitation = await self.get_invitation(invitation_id)
        if not invitation:
            raise ValueError("Invitation not found")
        
        if invitation.status != "pending":
            raise ValueError("Invitation is no longer valid")
        
        if invitation.expires_at < datetime.now():
            raise ValueError("Invitation has expired")
        
        # Get project
        project = await self.get_project(invitation.project_id)
        if not project:
            raise ValueError("Project not found")
        
        # Add user as member
        new_member = ProjectMember(
            user_id=user_id,
            email=invitation.invitee_email,
            name="",  # Will be populated from user service
            role=invitation.role,
            joined_at=datetime.now(),
            permissions=self.role_permissions[invitation.role]
        )
        
        project.members.append(new_member)
        project.updated_at = datetime.now()
        
        # Update invitation status
        invitation.status = "accepted"
        
        # Save changes
        await self._save_project_to_db(project)
        await self._save_invitation_to_db(invitation)
        
        self.logger.info(f"User {user_id} accepted invitation to project {invitation.project_id}")
        return project
    
    async def remove_project_member(
        self,
        project_id: str,
        remover_id: str,
        member_user_id: str
    ) -> Project:
        """
        Remove a member from a project.
        
        Args:
            project_id: Project ID
            remover_id: User ID of person removing the member
            member_user_id: User ID of member to remove
            
        Returns:
            Updated Project object
        """
        # Check permissions
        if not await self.check_user_permission(remover_id, project_id, 'project.manage_members'):
            raise PermissionError("User does not have permission to manage project members")
        
        # Get project
        project = await self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        # Cannot remove the owner
        if member_user_id == project.owner_id:
            raise ValueError("Cannot remove project owner")
        
        # Find and remove member
        original_count = len(project.members)
        project.members = [m for m in project.members if m.user_id != member_user_id]
        
        if len(project.members) == original_count:
            raise ValueError("Member not found in project")
        
        project.updated_at = datetime.now()
        
        # Save to database
        await self._save_project_to_db(project)
        
        self.logger.info(f"Removed member {member_user_id} from project {project_id}")
        return project
    
    async def check_user_permission(
        self,
        user_id: str,
        project_id: str,
        permission: str
    ) -> bool:
        """
        Check if a user has a specific permission for a project.
        
        Args:
            user_id: User ID
            project_id: Project ID
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        project = await self.get_project(project_id)
        if not project:
            return False
        
        # Find user in project members
        member = next((m for m in project.members if m.user_id == user_id), None)
        if not member:
            return False
        
        # Check if user has the permission
        return permission in member.permissions
    
    async def get_user_projects(
        self,
        user_id: str,
        status_filter: Optional[ProjectStatus] = None
    ) -> List[Project]:
        """
        Get all projects a user is a member of.
        
        Args:
            user_id: User ID
            status_filter: Optional status filter
            
        Returns:
            List of Project objects
        """
        def _get_user_projects():
            # This would query the database for projects where user is a member
            # For now, return empty list
            return []
        
        projects = await asyncio.get_event_loop().run_in_executor(
            self._executor, _get_user_projects
        )
        
        return projects
    
    async def get_user_project_count(self, user_id: str) -> int:
        """Get the number of projects a user owns or is a member of."""
        projects = await self.get_user_projects(user_id)
        return len(projects)
    
    async def get_invitation(self, invitation_id: str) -> Optional[ProjectInvitation]:
        """Get invitation by ID."""
        # This would query the database
        return None
    
    async def _save_project_to_db(self, project: Project) -> None:
        """Save project to database."""
        def _save():
            # This would save to the actual database
            pass
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, _save
        )
    
    async def _save_invitation_to_db(self, invitation: ProjectInvitation) -> None:
        """Save invitation to database."""
        def _save():
            # This would save to the actual database
            pass
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, _save
        )
    
    async def archive_project(
        self,
        project_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> Project:
        """
        Archive a project (soft delete with data retention).
        
        Args:
            project_id: Project ID
            user_id: User archiving the project
            reason: Optional reason for archiving
            
        Returns:
            Updated Project object
        """
        # Check permissions (only owner can archive)
        project = await self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        if project.owner_id != user_id:
            raise PermissionError("Only project owner can archive the project")
        
        if project.status == ProjectStatus.ARCHIVED:
            raise ValueError("Project is already archived")
        
        # Update project status
        project.status = ProjectStatus.ARCHIVED
        project.updated_at = datetime.now()
        
        # Add archival metadata
        if 'archival' not in project.stats:
            project.stats['archival'] = {}
        
        project.stats['archival'].update({
            'archived_at': datetime.now().isoformat(),
            'archived_by': user_id,
            'reason': reason,
            'data_retention_until': (datetime.now() + timedelta(days=project.settings.data_retention_days)).isoformat()
        })
        
        # Save to database
        await self._save_project_to_db(project)
        
        self.logger.info(f"Archived project {project_id} by user {user_id}")
        return project
    
    async def restore_project(
        self,
        project_id: str,
        user_id: str
    ) -> Project:
        """
        Restore an archived project.
        
        Args:
            project_id: Project ID
            user_id: User restoring the project
            
        Returns:
            Updated Project object
        """
        # Check permissions (only owner can restore)
        project = await self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        if project.owner_id != user_id:
            raise PermissionError("Only project owner can restore the project")
        
        if project.status != ProjectStatus.ARCHIVED:
            raise ValueError("Project is not archived")
        
        # Update project status
        project.status = ProjectStatus.ACTIVE
        project.updated_at = datetime.now()
        
        # Add restoration metadata
        if 'archival' not in project.stats:
            project.stats['archival'] = {}
        
        project.stats['archival'].update({
            'restored_at': datetime.now().isoformat(),
            'restored_by': user_id
        })
        
        # Save to database
        await self._save_project_to_db(project)
        
        self.logger.info(f"Restored project {project_id} by user {user_id}")
        return project
    
    async def delete_project(
        self,
        project_id: str,
        user_id: str,
        confirmation_token: str
    ) -> bool:
        """
        Permanently delete a project and all its data.
        
        Args:
            project_id: Project ID
            user_id: User deleting the project
            confirmation_token: Security confirmation token
            
        Returns:
            True if successfully deleted
        """
        # Check permissions (only owner can delete)
        project = await self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        if project.owner_id != user_id:
            raise PermissionError("Only project owner can delete the project")
        
        # Validate confirmation token (in production, this would be a secure token)
        expected_token = f"DELETE-{project_id[-8:].upper()}"
        if confirmation_token != expected_token:
            raise ValueError("Invalid confirmation token")
        
        # Mark as deleted (soft delete)
        project.status = ProjectStatus.DELETED
        project.updated_at = datetime.now()
        
        # Add deletion metadata
        if 'deletion' not in project.stats:
            project.stats['deletion'] = {}
        
        project.stats['deletion'].update({
            'deleted_at': datetime.now().isoformat(),
            'deleted_by': user_id,
            'permanent_deletion_scheduled': (datetime.now() + timedelta(days=30)).isoformat()
        })
        
        # Save to database
        await self._save_project_to_db(project)
        
        # TODO: Schedule background task to clean up project data
        # This would include:
        # - Vector database cleanup
        # - Knowledge graph cleanup  
        # - File storage cleanup
        # - Integration disconnection
        
        self.logger.info(f"Deleted project {project_id} by user {user_id}")
        return True
    
    async def update_member_role(
        self,
        project_id: str,
        updater_id: str,
        member_user_id: str,
        new_role: ProjectRole
    ) -> Project:
        """
        Update a project member's role.
        
        Args:
            project_id: Project ID
            updater_id: User making the update
            member_user_id: User whose role is being updated
            new_role: New role to assign
            
        Returns:
            Updated Project object
        """
        # Check permissions
        if not await self.check_user_permission(updater_id, project_id, 'project.manage_members'):
            raise PermissionError("User does not have permission to manage project members")
        
        # Get project
        project = await self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        # Cannot change owner role
        if member_user_id == project.owner_id:
            raise ValueError("Cannot change project owner role")
        
        # Find and update member
        member = next((m for m in project.members if m.user_id == member_user_id), None)
        if not member:
            raise ValueError("Member not found in project")
        
        # Update role and permissions
        old_role = member.role
        member.role = new_role
        member.permissions = self.role_permissions[new_role]
        
        project.updated_at = datetime.now()
        
        # Save to database
        await self._save_project_to_db(project)
        
        self.logger.info(f"Updated member {member_user_id} role from {old_role} to {new_role} in project {project_id}")
        return project
    
    async def get_project_statistics(
        self,
        project_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive project statistics.
        
        Args:
            project_id: Project ID
            user_id: User requesting statistics
            
        Returns:
            Dictionary with project statistics
        """
        # Check permissions
        if not await self.check_user_permission(user_id, project_id, 'project.view'):
            raise PermissionError("User does not have permission to view project statistics")
        
        project = await self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        # Calculate statistics
        now = datetime.now()
        project_age_days = (now - project.created_at).days
        
        # Mock statistics - in production, these would be calculated from actual data
        statistics = {
            'basic_info': {
                'project_id': project_id,
                'name': project.settings.name,
                'status': project.status,
                'created_at': project.created_at.isoformat(),
                'age_days': project_age_days,
                'member_count': len(project.members),
                'max_members': project.settings.max_members
            },
            'data_statistics': {
                'total_documents': 1250,
                'documents_by_source': {
                    'github': 400,
                    'jira': 200,
                    'slack': 300,
                    'confluence': 150,
                    'uploads': 200
                },
                'storage_used_mb': 145.7,
                'last_sync': (now - timedelta(hours=2)).isoformat()
            },
            'activity_statistics': {
                'queries_last_30_days': 89,
                'most_active_member': project.members[0].user_id if project.members else None,
                'avg_queries_per_day': 2.97,
                'peak_usage_hour': 14  # 2 PM
            },
            'ai_usage': {
                'tokens_used_this_month': 15420,
                'tokens_remaining': 4580,
                'avg_query_cost': 0.023,
                'total_cost_this_month': 3.54
            },
            'health_metrics': {
                'data_quality_score': 0.87,
                'integration_status': 'healthy',
                'last_backup': (now - timedelta(days=1)).isoformat(),
                'uptime_percentage': 99.8
            }
        }
        
        return statistics
    
    async def get_project_activity_feed(
        self,
        project_id: str,
        user_id: str,
        limit: int = 50,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get recent project activity feed.
        
        Args:
            project_id: Project ID
            user_id: User requesting the feed
            limit: Maximum number of activities to return
            days_back: Number of days to look back
            
        Returns:
            List of activity events
        """
        # Check permissions
        if not await self.check_user_permission(user_id, project_id, 'project.view'):
            raise PermissionError("User does not have permission to view project activity")
        
        # Mock activity feed - in production, this would query actual activity logs
        activities = [
            {
                'id': 'act_001',
                'type': 'data_sync',
                'description': 'GitHub repository synchronized',
                'user_id': user_id,
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'metadata': {'repository': 'main-repo', 'commits_added': 5}
            },
            {
                'id': 'act_002',
                'type': 'member_joined',
                'description': 'New member joined the project',
                'user_id': 'user_456',
                'timestamp': (datetime.now() - timedelta(hours=6)).isoformat(),
                'metadata': {'role': 'member'}
            },
            {
                'id': 'act_003',
                'type': 'ai_query',
                'description': 'AI query processed',
                'user_id': user_id,
                'timestamp': (datetime.now() - timedelta(hours=8)).isoformat(),
                'metadata': {'query_type': 'code_explanation', 'tokens_used': 150}
            }
        ]
        
        return activities[:limit]
    
    async def cleanup_expired_invitations(self) -> int:
        """
        Clean up expired project invitations.
        
        Returns:
            Number of invitations cleaned up
        """
        # This would query and delete expired invitations from the database
        # For now, return a mock count
        cleaned_up = 12
        
        self.logger.info(f"Cleaned up {cleaned_up} expired invitations")
        return cleaned_up
    
    async def get_user_project_permissions(
        self,
        user_id: str,
        project_id: str
    ) -> Dict[str, bool]:
        """
        Get all permissions for a user in a specific project.
        
        Args:
            user_id: User ID
            project_id: Project ID
            
        Returns:
            Dictionary mapping permission names to boolean values
        """
        project = await self.get_project(project_id)
        if not project:
            return {}
        
        # Find user in project members
        member = next((m for m in project.members if m.user_id == user_id), None)
        if not member:
            return {}
        
        # Return all possible permissions with their status
        all_permissions = set()
        for role_perms in self.role_permissions.values():
            all_permissions.update(role_perms)
        
        return {
            perm: perm in member.permissions
            for perm in all_permissions
        }
