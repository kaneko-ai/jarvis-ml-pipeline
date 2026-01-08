"""RBAC - Role-Based Access Control.

Per RP-418, implements role-based access control.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Permission(Enum):
    """Available permissions."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    RUN_QUERY = "run_query"
    VIEW_RESULTS = "view_results"
    EXPORT = "export"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT = "view_audit"


@dataclass
class Role:
    """A role with permissions."""

    role_id: str
    name: str
    permissions: set[Permission]
    description: str = ""


@dataclass
class User:
    """A user with roles."""

    user_id: str
    username: str
    roles: list[str]
    is_active: bool = True
    metadata: dict = field(default_factory=dict)


# Default roles
DEFAULT_ROLES = {
    "admin": Role(
        role_id="admin",
        name="Administrator",
        permissions={p for p in Permission},
        description="Full system access",
    ),
    "researcher": Role(
        role_id="researcher",
        name="Researcher",
        permissions={
            Permission.READ,
            Permission.RUN_QUERY,
            Permission.VIEW_RESULTS,
            Permission.EXPORT,
        },
        description="Research operations",
    ),
    "viewer": Role(
        role_id="viewer",
        name="Viewer",
        permissions={
            Permission.READ,
            Permission.VIEW_RESULTS,
        },
        description="Read-only access",
    ),
}


class RBAC:
    """Role-Based Access Control.
    
    Per RP-418:
    - Role definitions
    - Resource permissions
    - Admin UI
    """

    def __init__(self):
        self._roles: dict[str, Role] = dict(DEFAULT_ROLES)
        self._users: dict[str, User] = {}

    def create_role(
        self,
        role_id: str,
        name: str,
        permissions: list[Permission],
        description: str = "",
    ) -> Role:
        """Create a new role.
        
        Args:
            role_id: Role identifier.
            name: Display name.
            permissions: List of permissions.
            description: Role description.
            
        Returns:
            Created role.
        """
        role = Role(
            role_id=role_id,
            name=name,
            permissions=set(permissions),
            description=description,
        )
        self._roles[role_id] = role
        return role

    def get_role(self, role_id: str) -> Role | None:
        """Get a role by ID.
        
        Args:
            role_id: Role identifier.
            
        Returns:
            Role or None.
        """
        return self._roles.get(role_id)

    def create_user(
        self,
        user_id: str,
        username: str,
        roles: list[str],
    ) -> User:
        """Create a new user.
        
        Args:
            user_id: User identifier.
            username: Username.
            roles: List of role IDs.
            
        Returns:
            Created user.
        """
        user = User(
            user_id=user_id,
            username=username,
            roles=roles,
        )
        self._users[user_id] = user
        return user

    def get_user(self, user_id: str) -> User | None:
        """Get a user by ID.
        
        Args:
            user_id: User identifier.
            
        Returns:
            User or None.
        """
        return self._users.get(user_id)

    def assign_role(self, user_id: str, role_id: str) -> bool:
        """Assign a role to a user.
        
        Args:
            user_id: User identifier.
            role_id: Role identifier.
            
        Returns:
            True if assigned.
        """
        user = self._users.get(user_id)
        role = self._roles.get(role_id)

        if user and role:
            if role_id not in user.roles:
                user.roles.append(role_id)
            return True

        return False

    def remove_role(self, user_id: str, role_id: str) -> bool:
        """Remove a role from a user.
        
        Args:
            user_id: User identifier.
            role_id: Role identifier.
            
        Returns:
            True if removed.
        """
        user = self._users.get(user_id)

        if user and role_id in user.roles:
            user.roles.remove(role_id)
            return True

        return False

    def get_user_permissions(self, user_id: str) -> set[Permission]:
        """Get all permissions for a user.
        
        Args:
            user_id: User identifier.
            
        Returns:
            Set of permissions.
        """
        user = self._users.get(user_id)
        if not user or not user.is_active:
            return set()

        permissions = set()
        for role_id in user.roles:
            role = self._roles.get(role_id)
            if role:
                permissions.update(role.permissions)

        return permissions

    def check_permission(
        self,
        user_id: str,
        permission: Permission,
    ) -> bool:
        """Check if user has permission.
        
        Args:
            user_id: User identifier.
            permission: Permission to check.
            
        Returns:
            True if permitted.
        """
        permissions = self.get_user_permissions(user_id)
        return permission in permissions

    def require_permission(
        self,
        user_id: str,
        permission: Permission,
    ) -> None:
        """Require permission or raise.
        
        Args:
            user_id: User identifier.
            permission: Required permission.
            
        Raises:
            PermissionError if not permitted.
        """
        if not self.check_permission(user_id, permission):
            raise PermissionError(
                f"User {user_id} lacks permission: {permission.value}"
            )
