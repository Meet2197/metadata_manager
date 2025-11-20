# core/repositories/metadata_repository.py
from typing import List, Dict, Optional
from core.models.entities import Table, Database, Schema, Column
from .base_repository import BaseRepository
from django.db.models import Prefetch


class MetadataRepository(BaseRepository):
    """Repository for metadata operations"""
    
    def __init__(self):
        super().__init__(Table)
        
    def get_table_with_relations(self, table_id: str) -> Optional[Table]:
        """Get table with all related data"""
        return self.model_class.objects.select_related(
            'schema', 'database', 'owner'
        ).prefetch_related(
            'tags', 'column_entities', 'upstream_tables', 'downstream_tables'
        ).filter(id=table_id, deleted=False).first()
        
    def get_tables_by_database(self, database_id: str) -> List[Table]:
        """Get all tables in a database"""
        return self.model_class.objects.filter(
            database_id=database_id, deleted=False
        ).select_related('schema')
        
    def get_table_lineage(self, table_id: str, depth: int = 3) -> Dict:
        """Get table lineage up to specified depth"""
        table = self.get_by_id(table_id)
        if not table:
            return {}
            
        lineage = {
            'table': table,
            'upstream': self._get_upstream(table, depth),
            'downstream': self._get_downstream(table, depth)
        }
        return lineage
        
    def _get_upstream(self, table: Table, depth: int, visited=None) -> List:
        """Recursively get upstream tables"""
        if visited is None:
            visited = set()
        if depth == 0 or table.id in visited:
            return []
            
        visited.add(table.id)
        upstream = []
        
        for upstream_table in table.upstream_tables.filter(deleted=False):
            upstream.append({
                'table': upstream_table,
                'upstream': self._get_upstream(upstream_table, depth - 1, visited)
            })
        return upstream
        
    def _get_downstream(self, table: Table, depth: int, visited=None) -> List:
        """Recursively get downstream tables"""
        if visited is None:
            visited = set()
        if depth == 0 or table.id in visited:
            return []
            
        visited.add(table.id)
        downstream = []
        
        for downstream_table in table.downstream_tables.filter(deleted=False):
            downstream.append({
                'table': downstream_table,
                'downstream': self._get_downstream(downstream_table, depth - 1, visited)
            })
        return downstream
        
    def get_popular_tables(self, limit: int = 10) -> List[Table]:
        """Get most popular tables based on usage"""
        return self.model_class.objects.filter(
            deleted=False
        ).order_by('-usage_summary__queryCount')[:limit]