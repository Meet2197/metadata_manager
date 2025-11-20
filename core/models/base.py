# core/models/base.py
from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime

class BaseModel(models.Model):
    """Base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    version = models.IntegerField(default=1)
    deleted = models.BooleanField(default=False)
    
    class Meta:
        abstract = True
        
    def soft_delete(self):
        self.deleted = True
        self.save()


class EntityType(models.TextChoices):
    """Entity types in the metadata system"""
    TABLE = 'table', 'Table'
    DASHBOARD = 'dashboard', 'Dashboard'
    PIPELINE = 'pipeline', 'Pipeline'
    TOPIC = 'topic', 'Topic'
    DATABASE = 'database', 'Database'
    SCHEMA = 'schema', 'Schema'
    CONTAINER = 'container', 'Container'