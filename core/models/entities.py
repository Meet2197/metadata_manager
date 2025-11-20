# core/models/entities.py
from django.db import models
from .base import BaseModel, EntityType
import json

class DataSource(BaseModel):
    """Represents external metadata sources"""
    SOURCE_TYPES = [
        ('mysql', 'MySQL'),
        ('postgresql', 'PostgreSQL'),
        ('mongodb', 'MongoDB'),
        ('snowflake', 'Snowflake'),
        ('bigquery', 'BigQuery'),
        ('redshift', 'Redshift'),
        ('kafka', 'Apache Kafka'),
        ('s3', 'AWS S3'),
        ('api', 'REST API'),
    ]
    
    name = models.CharField(max_length=255, unique=True, db_index=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    connection_config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=50, default='pending')
    
    class Meta:
        db_table = 'data_sources'
        ordering = ['name']
        
    def __str__(self):
        return self.display_name


class Database(BaseModel):
    """Database entity"""
    name = models.CharField(max_length=255, db_index=True)
    fully_qualified_name = models.CharField(max_length=512, unique=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='databases')
    owner = models.ForeignKey('Owner', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    
    class Meta:
        db_table = 'databases'
        unique_together = ['name', 'data_source']
        
    def __str__(self):
        return self.fully_qualified_name


class Schema(BaseModel):
    """Schema/Namespace entity"""
    name = models.CharField(max_length=255, db_index=True)
    fully_qualified_name = models.CharField(max_length=512, unique=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    database = models.ForeignKey(Database, on_delete=models.CASCADE, related_name='schemas')
    
    class Meta:
        db_table = 'schemas'
        unique_together = ['name', 'database']
        
    def __str__(self):
        return self.fully_qualified_name


class Table(BaseModel):
    """Table entity - core metadata object"""
    TABLE_TYPES = [
        ('Regular', 'Regular Table'),
        ('View', 'View'),
        ('MaterializedView', 'Materialized View'),
        ('External', 'External Table'),
        ('Transient', 'Transient Table'),
    ]
    
    name = models.CharField(max_length=255, db_index=True)
    fully_qualified_name = models.CharField(max_length=512, unique=True, db_index=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    table_type = models.CharField(max_length=50, choices=TABLE_TYPES, default='Regular')
    
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE, related_name='tables')
    database = models.ForeignKey(Database, on_delete=models.CASCADE, related_name='tables')
    
    # Metadata
    columns = models.JSONField(default=list)  # Column definitions
    table_constraints = models.JSONField(default=list)  # Constraints
    table_partition = models.JSONField(null=True, blank=True)
    
    # Ownership and classification
    owner = models.ForeignKey('Owner', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    
    # Usage statistics
    usage_summary = models.JSONField(default=dict)
    profile_data = models.JSONField(default=dict)
    
    # Lineage
    upstream_tables = models.ManyToManyField('self', through='TableLineage', 
                                            symmetrical=False, related_name='downstream_tables')
    
    class Meta:
        db_table = 'tables'
        unique_together = ['name', 'schema']
        indexes = [
            models.Index(fields=['fully_qualified_name']),
            models.Index(fields=['schema', 'name']),
        ]
        
    def __str__(self):
        return self.fully_qualified_name


class Column(BaseModel):
    """Column metadata"""
    name = models.CharField(max_length=255, db_index=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='column_entities')
    data_type = models.CharField(max_length=100)
    data_type_display = models.CharField(max_length=255)
    
    ordinal_position = models.IntegerField()
    is_nullable = models.BooleanField(default=True)
    is_primary_key = models.BooleanField(default=False)
    is_foreign_key = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    
    default_value = models.TextField(blank=True, null=True)
    precision = models.IntegerField(null=True, blank=True)
    scale = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    
    # Data profiling
    profile = models.JSONField(default=dict)
    tags = models.ManyToManyField('Tag', blank=True)
    
    class Meta:
        db_table = 'columns'
        unique_together = ['table', 'name']
        ordering = ['ordinal_position']
        
    def __str__(self):
        return f"{self.table.fully_qualified_name}.{self.name}"


class Owner(BaseModel):
    """Owner entity for access control"""
    OWNER_TYPES = [
        ('user', 'User'),
        ('team', 'Team'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    owner_type = models.CharField(max_length=50, choices=OWNER_TYPES)
    email = models.EmailField(blank=True)
    profile = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'owners'
        
    def __str__(self):
        return self.display_name


class Tag(BaseModel):
    """Tag for classification"""
    name = models.CharField(max_length=255, unique=True, db_index=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey('TagCategory', on_delete=models.CASCADE, related_name='tags')
    style = models.JSONField(default=dict)  # Color, icon, etc.
    
    class Meta:
        db_table = 'tags'
        
    def __str__(self):
        return self.display_name


class TagCategory(BaseModel):
    """Tag category for grouping"""
    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'tag_categories'
        verbose_name_plural = 'Tag Categories'
        
    def __str__(self):
        return self.display_name