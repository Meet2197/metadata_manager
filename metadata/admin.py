# metadata/admin.py
from django.contrib import admin
from .models import (
    DataSource, Schema, Table, Column, DataLineage,
    Glossary, TableGlossaryMapping, DataQualityRule, DataQualityCheck
)

@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'host', 'is_active', 'created_at']
    list_filter = ['source_type', 'is_active']
    search_fields = ['name', 'description', 'host']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ['name', 'data_source', 'created_at']
    list_filter = ['data_source']
    search_fields = ['name', 'description']

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['name', 'schema', 'table_type', 'owner', 'row_count', 'created_at']
    list_filter = ['table_type', 'schema__data_source']
    search_fields = ['name', 'description', 'tags']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ['name', 'table', 'data_type', 'is_primary_key', 'is_foreign_key', 'is_nullable']
    list_filter = ['data_type', 'is_primary_key', 'is_foreign_key', 'is_nullable']
    search_fields = ['name', 'description']

@admin.register(DataLineage)
class DataLineageAdmin(admin.ModelAdmin):
    list_display = ['source_table', 'target_table', 'lineage_type', 'created_by', 'created_at']
    list_filter = ['lineage_type']
    search_fields = ['source_table__name', 'target_table__name', 'description']

@admin.register(Glossary)
class GlossaryAdmin(admin.ModelAdmin):
    list_display = ['term', 'category', 'owner', 'created_at']
    list_filter = ['category']
    search_fields = ['term', 'definition']
    filter_horizontal = ['related_terms']

@admin.register(DataQualityRule)
class DataQualityRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'table', 'column', 'rule_type', 'is_active']
    list_filter = ['rule_type', 'is_active']
    search_fields = ['name', 'table__name']

@admin.register(DataQualityCheck)
class DataQualityCheckAdmin(admin.ModelAdmin):
    list_display = ['rule', 'executed_at', 'passed', 'failed_count']
    list_filter = ['passed', 'executed_at']
    readonly_fields = ['executed_at']