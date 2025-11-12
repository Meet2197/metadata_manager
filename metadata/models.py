# metadata/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class DataSource(models.Model):
    """Represents a data source (database, API, file system, etc.)"""
    SOURCE_TYPES = [
        ('postgres', 'PostgreSQL'),
        ('mysql', 'MySQL'),
        ('mongodb', 'MongoDB'),
        ('api', 'REST API'),
        ('file', 'File System'),
        ('s3', 'AWS S3'),
        ('snowflake', 'Snowflake'),
        ('bigquery', 'BigQuery'),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    connection_string = models.CharField(max_length=500, blank=True)
    host = models.CharField(max_length=200, blank=True)
    port = models.IntegerField(null=True, blank=True)
    database_name = models.CharField(max_length=200, blank=True)
    username = models.CharField(max_length=200, blank=True)
    password = models.CharField(max_length=200, blank=True)  # Should be encrypted in production
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sources')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.source_type})"


class Schema(models.Model):
    """Represents a schema/database within a data source"""
    name = models.CharField(max_length=200)
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='schemas')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'data_source']
    
    def __str__(self):
        return f"{self.data_source.name}.{self.name}"


class Table(models.Model):
    """Represents a table/collection in a schema"""
    name = models.CharField(max_length=200)
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE, related_name='tables')
    description = models.TextField(blank=True)
    table_type = models.CharField(max_length=50, default='table', choices=[
        ('table', 'Table'),
        ('view', 'View'),
        ('materialized_view', 'Materialized View'),
    ])
    row_count = models.BigIntegerField(null=True, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_tables')
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'schema']
    
    def __str__(self):
        return f"{self.schema.data_source.name}.{self.schema.name}.{self.name}"
    
    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class Column(models.Model):
    """Represents a column in a table"""
    name = models.CharField(max_length=200)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='columns')
    data_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_primary_key = models.BooleanField(default=False)
    is_foreign_key = models.BooleanField(default=False)
    is_nullable = models.BooleanField(default=True)
    default_value = models.CharField(max_length=500, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    precision = models.IntegerField(null=True, blank=True)
    scale = models.IntegerField(null=True, blank=True)
    ordinal_position = models.IntegerField(default=0)
    tags = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['ordinal_position', 'name']
        unique_together = ['name', 'table']
    
    def __str__(self):
        return f"{self.table.name}.{self.name}"


class DataLineage(models.Model):
    """Represents data lineage between tables"""
    LINEAGE_TYPES = [
        ('etl', 'ETL Process'),
        ('view', 'View Definition'),
        ('manual', 'Manual Mapping'),
        ('foreign_key', 'Foreign Key'),
    ]
    
    source_table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='downstream_lineage')
    target_table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='upstream_lineage')
    lineage_type = models.CharField(max_length=50, choices=LINEAGE_TYPES)
    description = models.TextField(blank=True)
    transformation_logic = models.TextField(blank=True, help_text="SQL or transformation logic")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['source_table', 'target_table', 'lineage_type']
    
    def __str__(self):
        return f"{self.source_table} → {self.target_table}"


class DataQualityRule(models.Model):
    """Data quality rules for tables/columns"""
    RULE_TYPES = [
        ('not_null', 'Not Null'),
        ('unique', 'Unique Values'),
        ('range', 'Value Range'),
        ('pattern', 'Regex Pattern'),
        ('custom_sql', 'Custom SQL'),
    ]
    
    name = models.CharField(max_length=200)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='quality_rules')
    column = models.ForeignKey(Column, on_delete=models.CASCADE, null=True, blank=True, related_name='quality_rules')
    rule_type = models.CharField(max_length=50, choices=RULE_TYPES)
    rule_definition = models.TextField(help_text="Rule logic or SQL")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.table.name}"


class DataQualityCheck(models.Model):
    """Results of data quality checks"""
    rule = models.ForeignKey(DataQualityRule, on_delete=models.CASCADE, related_name='checks')
    executed_at = models.DateTimeField(auto_now_add=True)
    passed = models.BooleanField()
    failed_count = models.IntegerField(default=0)
    details = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-executed_at']
    
    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"{self.rule.name} - {status} - {self.executed_at}"


class Glossary(models.Model):
    """Business glossary terms"""
    term = models.CharField(max_length=200, unique=True)
    definition = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    related_terms = models.ManyToManyField('self', blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['term']
        verbose_name_plural = 'Glossaries'
    
    def __str__(self):
        return self.term


class TableGlossaryMapping(models.Model):
    """Maps glossary terms to tables/columns"""
    glossary_term = models.ForeignKey(Glossary, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, null=True, blank=True)
    column = models.ForeignKey(Column, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.column:
            return f"{self.glossary_term.term} → {self.column}"
        return f"{self.glossary_term.term} → {self.table}"