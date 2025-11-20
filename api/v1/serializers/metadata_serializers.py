# api/v1/serializers/metadata_serializers.py
from rest_framework import serializers
from core.models.entities import (
    DataSource, Database, Schema, Table, Column, 
    Owner, Tag, TagCategory
)
from core.models.relationships import TableLineage, GlossaryTerm


class OwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = ['id', 'name', 'display_name', 'owner_type', 'email', 'profile']


class TagSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'display_name', 'description', 'category', 'category_name', 'style']


class ColumnSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Column
        fields = [
            'id', 'name', 'display_name', 'description', 'data_type',
            'data_type_display', 'ordinal_position', 'is_nullable',
            'is_primary_key', 'is_foreign_key', 'is_unique',
            'default_value', 'precision', 'scale', 'max_length',
            'profile', 'tags'
        ]


class TableListSerializer(serializers.ModelSerializer):
    database_name = serializers.CharField(source='database.name', read_only=True)
    schema_name = serializers.CharField(source='schema.name', read_only=True)
    owner_name = serializers.CharField(source='owner.display_name', read_only=True)
    tag_count = serializers.IntegerField(source='tags.count', read_only=True)
    
    class Meta:
        model = Table
        fields = [
            'id', 'name', 'fully_qualified_name', 'display_name',
            'description', 'table_type', 'database_name', 'schema_name',
            'owner_name', 'tag_count', 'created_at', 'updated_at'
        ]


class TableDetailSerializer(serializers.ModelSerializer):
    database = serializers.CharField(source='database.name', read_only=True)
    schema = serializers.CharField(source='schema.name', read_only=True)
    owner = OwnerSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    column_entities = ColumnSerializer(many=True, read_only=True)
    
    class Meta:
        model = Table
        fields = [
            'id', 'name', 'fully_qualified_name', 'display_name',
            'description', 'table_type', 'database', 'schema',
            'columns', 'table_constraints', 'table_partition',
            'owner', 'tags', 'column_entities', 'usage_summary',
            'profile_data', 'version', 'created_at', 'updated_at'
        ]


class TableCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = [
            'name', 'display_name', 'description', 'table_type',
            'schema', 'database', 'columns', 'table_constraints',
            'owner', 'tags'
        ]


class DatabaseSerializer(serializers.ModelSerializer):
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    owner = OwnerSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    schema_count = serializers.IntegerField(source='schemas.count', read_only=True)
    table_count = serializers.IntegerField(source='tables.count', read_only=True)
    
    class Meta:
        model = Database
        fields = [
            'id', 'name', 'fully_qualified_name', 'display_name',
            'description', 'data_source_name', 'owner', 'tags',
            'schema_count', 'table_count', 'created_at', 'updated_at'
        ]


class SchemaSerializer(serializers.ModelSerializer):
    database_name = serializers.CharField(source='database.name', read_only=True)
    table_count = serializers.IntegerField(source='tables.count', read_only=True)
    
    class Meta:
        model = Schema
        fields = [
            'id', 'name', 'fully_qualified_name', 'display_name',
            'description', 'database_name', 'table_count',
            'created_at', 'updated_at'
        ]


class DataSourceSerializer(serializers.ModelSerializer):
    database_count = serializers.IntegerField(source='databases.count', read_only=True)
    
    class Meta:
        model = DataSource
        fields = [
            'id', 'name', 'display_name', 'description', 'source_type',
            'is_active', 'last_sync', 'sync_status', 'database_count',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'connection_config': {'write_only': True}
        }


class TableLineageSerializer(serializers.ModelSerializer):
    upstream_table_name = serializers.CharField(source='upstream_table.fully_qualified_name', read_only=True)
    downstream_table_name = serializers.CharField(source='downstream_table.fully_qualified_name', read_only=True)
    
    class Meta:
        model = TableLineage
        fields = [
            'id', 'upstream_table', 'downstream_table',
            'upstream_table_name', 'downstream_table_name',
            'lineage_type', 'column_lineage', 'sql_query',
            'description', 'created_at'
        ]


class GlossaryTermSerializer(serializers.ModelSerializer):
    glossary_name = serializers.CharField(source='glossary.display_name', read_only=True)
    owner = OwnerSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    related_terms = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = GlossaryTerm
        fields = [
            'id', 'name', 'display_name', 'description',
            'glossary', 'glossary_name', 'parent', 'related_terms',
            'synonyms', 'owner', 'tags', 'references',
            'created_at', 'updated_at'
        ]