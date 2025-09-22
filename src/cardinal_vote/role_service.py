"""
Role Service for Cardinal Vote.

This service handles role-based access control (RBAC) including
user role management, permission checking, and access control logic.
"""

from typing import Dict, List, Any, Optional, Set
from enum import Enum
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .database_manager import GeneralizedDatabaseManager
from .models import User, Vote, VoteOption


class Permission(Enum):
    """System permissions."""

    # Vote permissions
    CREATE_VOTE = "create_vote"
    VIEW_VOTE = "view_vote"
    EDIT_OWN_VOTE = "edit_own_vote"
    DELETE_OWN_VOTE = "delete_own_vote"
    PUBLISH_OWN_VOTE = "publish_own_vote"
    PARTICIPATE_VOTE = "participate_vote"

    # Admin vote permissions
    VIEW_ANY_VOTE = "view_any_vote"
    EDIT_ANY_VOTE = "edit_any_vote"
    DELETE_ANY_VOTE = "delete_any_vote"
    PUBLISH_ANY_VOTE = "publish_any_vote"

    # Dashboard permissions
    VIEW_USER_DASHBOARD = "view_user_dashboard"
    VIEW_ADMIN_DASHBOARD = "view_admin_dashboard"
    VIEW_USER_STATS = "view_user_stats"
    VIEW_SYSTEM_STATS = "view_system_stats"

    # User management permissions
    VIEW_USER_LIST = "view_user_list"
    EDIT_USER_PROFILE = "edit_user_profile"
    DELETE_USER = "delete_user"
    CHANGE_USER_ROLE = "change_user_role"

    # System permissions
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_SYSTEM_CONFIG = "manage_system_config"
    SEND_SYSTEM_ANNOUNCEMENTS = "send_system_announcements"


class RoleService:
    """Service for managing roles and permissions."""

    def __init__(self, db_manager: GeneralizedDatabaseManager):
        self.db_manager = db_manager
        self._role_permissions = self._initialize_role_permissions()

    def _initialize_role_permissions(self) -> Dict[UserRole, Set[Permission]]:
        """
        Initialize role-based permissions mapping.

        Returns:
            Dictionary mapping roles to their permissions
        """
        return {
            UserRole.USER: {
                # Basic user permissions
                Permission.CREATE_VOTE,
                Permission.VIEW_VOTE,
                Permission.EDIT_OWN_VOTE,
                Permission.DELETE_OWN_VOTE,
                Permission.PUBLISH_OWN_VOTE,
                Permission.PARTICIPATE_VOTE,
                Permission.VIEW_USER_DASHBOARD,
                Permission.VIEW_USER_STATS,
                Permission.EDIT_USER_PROFILE,
            },
            UserRole.ADMIN: {
                # All user permissions plus admin permissions
                Permission.CREATE_VOTE,
                Permission.VIEW_VOTE,
                Permission.EDIT_OWN_VOTE,
                Permission.DELETE_OWN_VOTE,
                Permission.PUBLISH_OWN_VOTE,
                Permission.PARTICIPATE_VOTE,
                Permission.VIEW_USER_DASHBOARD,
                Permission.VIEW_USER_STATS,
                Permission.EDIT_USER_PROFILE,
                # Admin-specific permissions
                Permission.VIEW_ANY_VOTE,
                Permission.EDIT_ANY_VOTE,
                Permission.DELETE_ANY_VOTE,
                Permission.PUBLISH_ANY_VOTE,
                Permission.VIEW_ADMIN_DASHBOARD,
                Permission.VIEW_SYSTEM_STATS,
                Permission.VIEW_USER_LIST,
                Permission.DELETE_USER,
                Permission.CHANGE_USER_ROLE,
                Permission.VIEW_SYSTEM_LOGS,
                Permission.MANAGE_SYSTEM_CONFIG,
                Permission.SEND_SYSTEM_ANNOUNCEMENTS,
            },
        }

    def has_permission(self, user: User, permission: Permission) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user: The user to check
            permission: The permission to check for

        Returns:
            True if user has the permission
        """
        if not user or not user.role:
            return False

        user_permissions = self._role_permissions.get(user.role, set())
        return permission in user_permissions

    def has_any_permission(self, user: User, permissions: List[Permission]) -> bool:
        """
        Check if a user has any of the specified permissions.

        Args:
            user: The user to check
            permissions: List of permissions to check

        Returns:
            True if user has at least one of the permissions
        """
        return any(self.has_permission(user, permission) for permission in permissions)

    def has_all_permissions(self, user: User, permissions: List[Permission]) -> bool:
        """
        Check if a user has all of the specified permissions.

        Args:
            user: The user to check
            permissions: List of permissions to check

        Returns:
            True if user has all the permissions
        """
        return all(self.has_permission(user, permission) for permission in permissions)

    def get_user_permissions(self, user: User) -> Set[Permission]:
        """
        Get all permissions for a user.

        Args:
            user: The user to get permissions for

        Returns:
            Set of permissions the user has
        """
        if not user or not user.role:
            return set()

        return self._role_permissions.get(user.role, set())

    def can_access_dashboard(self, user: User, dashboard_type: str = "user") -> bool:
        """
        Check if a user can access a specific dashboard type.

        Args:
            user: The user to check
            dashboard_type: Type of dashboard ("user" or "admin")

        Returns:
            True if user can access the dashboard
        """
        if dashboard_type == "admin":
            return self.has_permission(user, Permission.VIEW_ADMIN_DASHBOARD)
        else:
            return self.has_permission(user, Permission.VIEW_USER_DASHBOARD)

    def can_access_statistics(self, user: User, scope: str = "user") -> bool:
        """
        Check if a user can access statistics with the specified scope.

        Args:
            user: The user to check
            scope: Statistics scope ("user" or "system")

        Returns:
            True if user can access the statistics
        """
        if scope == "system":
            return self.has_permission(user, Permission.VIEW_SYSTEM_STATS)
        else:
            return self.has_permission(user, Permission.VIEW_USER_STATS)

    async def can_access_vote(
        self, user: User, vote: Vote, action: str = "view"
    ) -> bool:
        """
        Check if a user can perform an action on a specific vote.

        Args:
            user: The user to check
            vote: The vote to check access for
            action: The action to perform ("view", "edit", "delete", "publish")

        Returns:
            True if user can perform the action on the vote
        """
        if not user or not vote:
            return False

        # Check if user is the vote creator
        is_creator = str(user.id) == vote.creator_id

        if action == "view":
            # Anyone can view published votes
            if vote.status == VoteStatus.ACTIVE:
                return self.has_permission(user, Permission.VIEW_VOTE)
            # Only creator or admin can view draft/completed votes
            elif is_creator:
                return self.has_permission(user, Permission.VIEW_VOTE)
            else:
                return self.has_permission(user, Permission.VIEW_ANY_VOTE)

        elif action == "edit":
            if is_creator:
                return self.has_permission(user, Permission.EDIT_OWN_VOTE)
            else:
                return self.has_permission(user, Permission.EDIT_ANY_VOTE)

        elif action == "delete":
            if is_creator:
                return self.has_permission(user, Permission.DELETE_OWN_VOTE)
            else:
                return self.has_permission(user, Permission.DELETE_ANY_VOTE)

        elif action == "publish":
            if is_creator:
                return self.has_permission(user, Permission.PUBLISH_OWN_VOTE)
            else:
                return self.has_permission(user, Permission.PUBLISH_ANY_VOTE)

        elif action == "participate":
            # Users can't participate in their own votes
            if is_creator:
                return False
            # Only published votes can be participated in
            if vote.status != VoteStatus.ACTIVE:
                return False
            return self.has_permission(user, Permission.PARTICIPATE_VOTE)

        return False

    async def can_manage_user(
        self, acting_user: User, target_user: User, action: str
    ) -> bool:
        """
        Check if a user can manage another user.

        Args:
            acting_user: The user trying to perform the action
            target_user: The user being acted upon
            action: The action to perform ("view", "edit", "delete", "change_role")

        Returns:
            True if the action is allowed
        """
        if not acting_user or not target_user:
            return False

        # Users can always manage their own profile
        if str(acting_user.id) == str(target_user.id) and action in ["view", "edit"]:
            return self.has_permission(acting_user, Permission.EDIT_USER_PROFILE)

        # Admin permissions required for managing other users
        if action == "view":
            return self.has_permission(acting_user, Permission.VIEW_USER_LIST)
        elif action == "delete":
            # Can't delete yourself
            if str(acting_user.id) == str(target_user.id):
                return False
            return self.has_permission(acting_user, Permission.DELETE_USER)
        elif action == "change_role":
            # Can't change your own role
            if str(acting_user.id) == str(target_user.id):
                return False
            return self.has_permission(acting_user, Permission.CHANGE_USER_ROLE)

        return False

    async def get_accessible_votes(
        self,
        user: User,
        session: AsyncSession,
        include_drafts: bool = False,
        created_only: bool = False,
    ) -> List[Vote]:
        """
        Get all votes a user can access.

        Args:
            user: The user to get votes for
            session: Database session
            include_drafts: Whether to include draft votes
            created_only: Whether to only include votes created by the user

        Returns:
            List of accessible votes
        """
        if not user:
            return []

        query = select(Vote)

        if created_only:
            # Only votes created by the user
            query = query.where(Vote.creator_id == str(user.id))
        elif self.has_permission(user, Permission.VIEW_ANY_VOTE):
            # Admin can see all votes
            pass
        else:
            # Regular users can see their own votes and published votes
            query = query.where(
                or_(Vote.creator_id == str(user.id), Vote.status == VoteStatus.ACTIVE)
            )

        if not include_drafts and not self.has_permission(
            user, Permission.VIEW_ANY_VOTE
        ):
            # Only include drafts for admins or when explicitly requested
            query = query.where(Vote.status != VoteStatus.DRAFT)

        result = await session.execute(query)
        return result.scalars().all()

    async def get_user_role_summary(self, user: User) -> Dict[str, Any]:
        """
        Get a summary of a user's role and permissions.

        Args:
            user: The user to get role summary for

        Returns:
            Dictionary containing role and permission information
        """
        if not user:
            return {
                "role": None,
                "permissions": [],
                "can_access_admin": False,
                "can_manage_users": False,
                "can_view_system_stats": False,
            }

        permissions = self.get_user_permissions(user)
        permission_list = [perm.value for perm in permissions]

        return {
            "role": user.role.value if user.role else None,
            "permissions": permission_list,
            "can_access_admin": self.has_permission(
                user, Permission.VIEW_ADMIN_DASHBOARD
            ),
            "can_manage_users": self.has_permission(user, Permission.DELETE_USER),
            "can_view_system_stats": self.has_permission(
                user, Permission.VIEW_SYSTEM_STATS
            ),
            "can_send_announcements": self.has_permission(
                user, Permission.SEND_SYSTEM_ANNOUNCEMENTS
            ),
            "permission_count": len(permissions),
        }

    def require_permission(self, user: User, permission: Permission):
        """
        Decorator/context helper to require a specific permission.
        Raises an exception if the user doesn't have the permission.

        Args:
            user: The user to check
            permission: The required permission

        Raises:
            PermissionError: If user lacks the permission
        """
        if not self.has_permission(user, permission):
            raise PermissionError(
                f"User {user.username if user else 'None'} lacks required permission: {permission.value}"
            )

    def require_any_permission(self, user: User, permissions: List[Permission]):
        """
        Require that the user has at least one of the specified permissions.

        Args:
            user: The user to check
            permissions: List of permissions (user needs at least one)

        Raises:
            PermissionError: If user lacks all permissions
        """
        if not self.has_any_permission(user, permissions):
            permission_names = [perm.value for perm in permissions]
            raise PermissionError(
                f"User {user.username if user else 'None'} lacks required permissions: {permission_names}"
            )

    async def audit_user_access(
        self, user: User, resource_type: str, resource_id: str, action: str
    ) -> None:
        """
        Audit user access attempts (placeholder for future implementation).

        Args:
            user: The user performing the action
            resource_type: Type of resource being accessed
            resource_id: ID of the resource
            action: Action being performed
        """
        # Placeholder for audit logging
        # In a full implementation, this would log to an audit table
        pass

    def get_role_hierarchy(self) -> Dict[str, int]:
        """
        Get role hierarchy for comparison purposes.

        Returns:
            Dictionary mapping role names to hierarchy levels
        """
        return {UserRole.USER.value: 1, UserRole.ADMIN.value: 10}

    def is_higher_role(self, user1: User, user2: User) -> bool:
        """
        Check if user1 has a higher role than user2.

        Args:
            user1: First user to compare
            user2: Second user to compare

        Returns:
            True if user1 has a higher role than user2
        """
        if not user1 or not user2 or not user1.role or not user2.role:
            return False

        hierarchy = self.get_role_hierarchy()
        level1 = hierarchy.get(user1.role.value, 0)
        level2 = hierarchy.get(user2.role.value, 0)

        return level1 > level2
