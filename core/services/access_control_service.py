# core/services/access_control_service.py
from typing import List, Optional
from django.contrib.auth.models import User, Group, Permission
from core.models.entities import Owner
import logging

logger = logging.getLogger(__name__)


class AccessControlService:
    """Service for access control and permissions"""
    
    def __init__(self):
        pass
        
    def check_permission(self, user: User, entity_type: str, 
                        entity_id: str, action: str) -> bool:
        """Check if user has permission for action on entity"""
        try:
            # Check if user is superuser
            if user.is_superuser:
                return True
                
            # Check entity ownership
            if self._is_owner(user, entity_type, entity_id):
                return True
                
            # Check group permissions
            permission = f"{entity_type}.{action}"
            if user.has_perm(permission):
                return True
                
            # Check role-based permissions
            if self._check_role_permission(user, entity_type, action):
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            return False
            
    def grant_permission(self, user: User, entity_type: str, 
                        entity_id: str, action: str) -> bool:
        """Grant permission to user"""
        try:
            permission, created = Permission.objects.get_or_create(
                codename=f"{action}_{entity_type}",
                name=f"Can {action} {entity_type}",
                content_type_id=self._get_content_type_id(entity_type)
            )
            user.user_permissions.add(permission)
            return True
        except Exception as e:
            logger.error(f"Grant permission error: {str(e)}")
            return False
            
    def revoke_permission(self, user: User, entity_type: str, 
                         entity_id: str, action: str) -> bool:
        """Revoke permission from user"""
        try:
            permission = Permission.objects.get(
                codename=f"{action}_{entity_type}"
            )
            user.user_permissions.remove(permission)
            return True
        except Exception as e:
            logger.error(f"Revoke permission error: {str(e)}")
            return False
            
    def get_user_permissions(self, user: User) -> List[str]:
        """Get all permissions for user"""
        return list(user.get_all_permissions())
        
    def _is_owner(self, user: User, entity_type: str, entity_id: str) -> bool:
        """Check if user is owner of entity"""
        # Implementation depends on entity type
        return False
        
    def _check_role_permission(self, user: User, entity_type: str, action: str) -> bool:
        """Check role-based permissions"""
        # Implementation for role-based access control
        return False
        
    def _get_content_type_id(self, entity_type: str) -> int:
        """Get content type ID for entity type"""
        from django.contrib.contenttypes.models import ContentType
        from core.models.entities import Table, Database, Schema
        
        model_map = {
            'table': Table,
            'database': Database,
            'schema': Schema,
        }
        
        model = model_map.get(entity_type)
        if model:
            return ContentType.objects.get_for_model(model).id
        return None