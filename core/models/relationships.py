# core/models/relationships.py
from django.db import models
from .base import BaseModel
from .entities import Table

class TableLineage(BaseModel):
    """Table lineage relationship"""
    LINEAGE_TYPES = [
        ('ETL', 'ETL Process'),
        ('VIEW', 'View Definition'),
        ('CLONE', 'Table Clone'),
        ('MANUAL', 'Manual Mapping'),
    ]
    
    upstream_table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='lineage_downstream')
    downstream_table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='lineage_upstream')
    lineage_type = models.CharField(max_length=50, choices=LINEAGE_TYPES)
    
    # Optional: Column-level lineage
    column_lineage = models.JSONField(default=list)
    
    # Transformation logic
    sql_query = models.TextField(blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'table_lineage'
        unique_together = ['upstream_table', 'downstream_table']
        
    def __str__(self):
        return f"{self.upstream_table} → {self.downstream_table}"


class ChangeEvent(BaseModel):
    """Change event for audit trail"""
    EVENT_TYPES = [
        ('entity_created', 'Entity Created'),
        ('entity_updated', 'Entity Updated'),
        ('entity_deleted', 'Entity Deleted'),
        ('entity_soft_deleted', 'Entity Soft Deleted'),
    ]
    
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField(db_index=True)
    entity_fqn = models.CharField(max_length=512)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    
    previous_version = models.JSONField(null=True, blank=True)
    current_version = models.JSONField()
    change_description = models.JSONField(default=dict)
    
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'change_events'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']


class GlossaryTerm(BaseModel):
    """Business glossary term"""
    name = models.CharField(max_length=255, unique=True, db_index=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField()
    
    # Relationships
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    related_terms = models.ManyToManyField('self', blank=True)
    synonyms = models.JSONField(default=list)
    
    # Metadata
    glossary = models.ForeignKey('Glossary', on_delete=models.CASCADE, related_name='terms')
    tags = models.ManyToManyField('Tag', blank=True)
    owner = models.ForeignKey('Owner', on_delete=models.SET_NULL, null=True)
    
    # References
    references = models.JSONField(default=list)
    
    class Meta:
        db_table = 'glossary_terms'
        
    def __str__(self):
        return self.display_name


class Glossary(BaseModel):
    """Glossary container"""
    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey('Owner', on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField('Tag', blank=True)
    
    class Meta:
        db_table = 'glossaries'
        verbose_name_plural = 'Glossaries'
        
    def __str__(self):
        return self.display_name