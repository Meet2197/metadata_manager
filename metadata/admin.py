# metadata/admin.py
from django.contrib import admin
from .models import DataSource, Schema, Table, Column, DataLineage, Glossary, DataQualityRule, DataQualityCheck

@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    # Fixes admin.E108, admin.E116: Replaces old fields with new file/metadata fields
    list_display = (
        'name', 
        'status', 
        'upload_date', 
        'get_file_name_display' # Custom method to display file name
    )

    # Fixes admin.E116: Only filter by fields that exist
    list_filter = ('status',) 
    
    search_fields = ('name', 'description')
    
    # Fixes admin.E035: Makes the UUID and date fields read-only
    readonly_fields = (
        'uuid', 
        'status', 
        'upload_date', 
        'uploaded_file',
        'processed_metadata'
    )
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'uploaded_file', 'uuid', 'upload_date', 'status')
        }),
        ('Metadata Details', {
            'fields': ('processed_metadata',),
            'classes': ('collapse',),
        })
    )

    # Custom method to display the uploaded file name
    def get_file_name_display(self, obj):
        if obj.uploaded_file:
            return obj.uploaded_file.name.split('/')[-1]
        return "N/A"
    get_file_name_display.short_description = 'File Name'
    
    # NOTE: You will need to similarly update the admin classes for 
    # Table, Column, etc., if their models also changed.

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