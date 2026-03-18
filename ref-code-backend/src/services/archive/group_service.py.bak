"""
Group and role service for managing groups, roles, and permissions.
"""

import logging
from typing import Optional, List

from database.repositories.group_repository import GroupRepository
from models.group import Group, GroupCreate, GroupUpdate, Role, RoleCreate

logger = logging.getLogger(__name__)


class GroupService:
    """Service for group and role operations."""
    
    # ========== Group Operations ==========
    
    @staticmethod
    def create_group(group_create: GroupCreate) -> Group:
        """
        Create a new group.
        
        Args:
            group_create: GroupCreate model with group data
            
        Returns:
            Created Group object
            
        Raises:
            ValueError: If group name already exists
        """
        # Check if group name exists
        if GroupRepository.get_group_by_name(group_create.name):
            raise ValueError(f"Group '{group_create.name}' already exists")
        
        group_dict = GroupRepository.create_group(
            name=group_create.name,
            description=group_create.description
        )
        
        logger.info(f"Group created: {group_create.name} (ID: {group_dict['id']})")
        return Group(**group_dict)
    
    @staticmethod
    def get_group_by_id(group_id: int) -> Optional[Group]:
        """Get group by ID."""
        group_dict = GroupRepository.get_group_by_id(group_id)
        return Group(**group_dict) if group_dict else None
    
    @staticmethod
    def get_group_by_name(name: str) -> Optional[Group]:
        """Get group by name."""
        group_dict = GroupRepository.get_group_by_name(name)
        return Group(**group_dict) if group_dict else None
    
    @staticmethod
    def get_all_groups(active_only: bool = True) -> List[Group]:
        """Get all groups."""
        groups_dict = GroupRepository.get_all_groups(active_only=active_only)
        return [Group(**g) for g in groups_dict]
    
    @staticmethod
    def update_group(group_id: int, group_update: GroupUpdate) -> Optional[Group]:
        """
        Update group information.
        
        Args:
            group_id: Group ID
            group_update: GroupUpdate model with fields to update
            
        Returns:
            Updated Group object or None if not found
        """
        update_data = group_update.model_dump(exclude_unset=True)
        if not update_data:
            return GroupService.get_group_by_id(group_id)
        
        group_dict = GroupRepository.update_group(group_id, **update_data)
        return Group(**group_dict) if group_dict else None
    
    @staticmethod
    def delete_group(group_id: int) -> bool:
        """
        Delete (deactivate) a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            True if successful, False otherwise
        """
        success = GroupRepository.delete_group(group_id)
        if success:
            logger.info(f"Group {group_id} deleted")
        return success
    
    @staticmethod
    def get_group_users(group_id: int) -> List:
        """
        Get all users in a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            List of user dictionaries
        """
        return GroupRepository.get_group_users(group_id)
    
    # ========== Role Operations ==========
    
    @staticmethod
    def create_role(role_create: RoleCreate) -> Role:
        """
        Create a new role.
        
        Args:
            role_create: RoleCreate model with role data
            
        Returns:
            Created Role object
            
        Raises:
            ValueError: If role name already exists
        """
        # Check if role name exists
        if GroupRepository.get_role_by_name(role_create.name):
            raise ValueError(f"Role '{role_create.name}' already exists")
        
        role_dict = GroupRepository.create_role(
            name=role_create.name,
            description=role_create.description,
            permissions=role_create.permissions
        )
        
        logger.info(f"Role created: {role_create.name} (ID: {role_dict['id']})")
        return Role(**role_dict)
    
    @staticmethod
    def get_role_by_id(role_id: int) -> Optional[Role]:
        """Get role by ID."""
        role_dict = GroupRepository.get_role_by_id(role_id)
        return Role(**role_dict) if role_dict else None
    
    @staticmethod
    def get_role_by_name(name: str) -> Optional[Role]:
        """Get role by name."""
        role_dict = GroupRepository.get_role_by_name(name)
        return Role(**role_dict) if role_dict else None
    
    @staticmethod
    def get_all_roles() -> List[Role]:
        """Get all roles."""
        roles_dict = GroupRepository.get_all_roles()
        return [Role(**r) for r in roles_dict]
    
    # ========== Group-Role Associations ==========
    
    @staticmethod
    def assign_role_to_group(group_id: int, role_id: int) -> bool:
        """
        Assign a role to a group.
        
        Args:
            group_id: Group ID
            role_id: Role ID
            
        Returns:
            True if successful, False otherwise
        """
        success = GroupRepository.assign_role_to_group(group_id, role_id)
        if success:
            logger.info(f"Role {role_id} assigned to group {group_id}")
        return success
    
    @staticmethod
    def remove_role_from_group(group_id: int, role_id: int) -> bool:
        """
        Remove a role from a group.
        
        Args:
            group_id: Group ID
            role_id: Role ID
            
        Returns:
            True if successful, False otherwise
        """
        success = GroupRepository.remove_role_from_group(group_id, role_id)
        if success:
            logger.info(f"Role {role_id} removed from group {group_id}")
        return success
    
    @staticmethod
    def get_group_roles(group_id: int) -> List[Role]:
        """Get all roles for a group."""
        roles_dict = GroupRepository.get_group_roles(group_id)
        return [Role(**r) for r in roles_dict]
    
    @staticmethod
    def get_user_roles(user_id: int) -> List[Role]:
        """Get all roles for a user (through their groups)."""
        roles_dict = GroupRepository.get_user_roles(user_id)
        return [Role(**r) for r in roles_dict]
    
    # ========== Permission Checks ==========
    
    @staticmethod
    def check_permission(user_id: int, permission: str) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: User ID
            permission: Permission string to check (e.g., 'read:corpus')
            
        Returns:
            True if user has permission, False otherwise
        """
        roles = GroupService.get_user_roles(user_id)
        
        for role in roles:
            if not role.permissions:
                continue
            
            # Check for wildcard permission
            if "*" in role.permissions:
                return True
            
            # Check for exact permission match
            if permission in role.permissions:
                return True
            
            # Check for prefix match (e.g., 'read:*' matches 'read:corpus')
            permission_parts = permission.split(':')
            if len(permission_parts) == 2:
                prefix_wildcard = f"{permission_parts[0]}:*"
                if prefix_wildcard in role.permissions:
                    return True
        
        return False
