# core/services/metadata_service.py
from typing import Dict, List, Optional, Any
from core.repositories.metadata_repository import MetadataRepository
from core.models.entities import Table, Database, Schema
from core.models.relationships import ChangeEvent
from events.change_event_handler import ChangeEventHandler
from search.indexer import SearchIndexer
import logging

logger = logging.getLogger(__name__)


class MetadataService:
    """Service for metadata operations"""
    
    def __init__(self):
        self.repository = MetadataRepository()
        self.event_handler = ChangeEventHandler()
        self.indexer = SearchIndexer()
        
    def create_table(self, data: Dict, user: Any) -> Table:
        """Create a new table entity"""
        try:
            # Validate required fields
            self._validate_table_data(data)
            
            # Create table
            data['created_by'] = user
            table = self.repository.create(**data)
            
            # Publish change event
            self.event_handler.publish_event(
                entity_type='table',
                entity_id=str(table.id),
                entity_fqn=table.fully_qualified_name,
                event_type='entity_created',
                current_version=self._serialize_table(table),
                user=user
            )
            
            # Index for search
            self.indexer.index_entity(table)
            
            logger.info(f"Table created: {table.fully_qualified_name}")
            return table
            
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            raise
            
    def update_table(self, table_id: str, data: Dict, user: Any) -> Optional[Table]:
        """Update table entity"""
        try:
            # Get existing table
            existing_table = self.repository.get_by_id(table_id)
            if not existing_table:
                return None
                
            previous_version = self._serialize_table(existing_table)
            
            # Update table
            data['updated_by'] = user
            table = self.repository.update(table_id, **data)
            
            # Publish change event
            self.event_handler.publish_event(
                entity_type='table',
                entity_id=str(table.id),
                entity_fqn=table.fully_qualified_name,
                event_type='entity_updated',
                previous_version=previous_version,
                current_version=self._serialize_table(table),
                user=user
            )
            
            # Re-index
            self.indexer.update_entity(table)
            
            logger.info(f"Table updated: {table.fully_qualified_name}")
            return table
            
        except Exception as e:
            logger.error(f"Error updating table: {str(e)}")
            raise
            
    def delete_table(self, table_id: str, user: Any, hard: bool = False) -> bool:
        """Delete table entity"""
        try:
            table = self.repository.get_by_id(table_id)
            if not table:
                return False
                
            previous_version = self._serialize_table(table)
            
            # Delete table
            success = self.repository.delete(table_id, soft=not hard)
            
            if success:
                # Publish change event
                self.event_handler.publish_event(
                    entity_type='table',
                    entity_id=str(table.id),
                    entity_fqn=table.fully_qualified_name,
                    event_type='entity_deleted' if hard else 'entity_soft_deleted',
                    previous_version=previous_version,
                    current_version=None,
                    user=user
                )
                
                # Remove from index
                self.indexer.delete_entity(table.id)
                
            return success
            
        except Exception as e:
            logger.error(f"Error deleting table: {str(e)}")
            raise
            
    def get_table(self, table_id: str) -> Optional[Table]:
        """Get table by ID with all relations"""
        return self.repository.get_table_with_relations(table_id)
        
    def get_table_by_fqn(self, fqn: str) -> Optional[Table]:
        """Get table by fully qualified name"""
        return self.repository.get_by_fqn(fqn)
        
    def get_table_lineage(self, table_id: str, depth: int = 3) -> Dict:
        """Get table lineage"""
        return self.repository.get_table_lineage(table_id, depth)
        
    def add_table_lineage(self, upstream_id: str, downstream_id: str, 
                         lineage_type: str, sql_query: str = '', user: Any = None) -> bool:
        """Add lineage between tables"""
        from core.models.relationships import TableLineage
        
        try:
            lineage = TableLineage.objects.create(
                upstream_table_id=upstream_id,
                downstream_table_id=downstream_id,
                lineage_type=lineage_type,
                sql_query=sql_query,
                created_by=user
            )
            
            logger.info(f"Lineage created: {lineage}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating lineage: {str(e)}")
            return False
            
    def search_tables(self, query: str, filters: Dict = None) -> List[Table]:
        """Search tables"""
        return self.indexer.search_entities('table', query, filters)
        
    def get_popular_tables(self, limit: int = 10) -> List[Table]:
        """Get popular tables"""
        return self.repository.get_popular_tables(limit)
        
    def _validate_table_data(self, data: Dict):
        """Validate table data"""
        required_fields = ['name', 'schema_id']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
                
    def _serialize_table(self, table: Table) -> Dict:
        """Serialize table to dict"""
        return {
            'id': str(table.id),
            'name': table.name,
            'fully_qualified_name': table.fully_qualified_name,
            'description': table.description,
            'table_type': table.table_type,
            'columns': table.columns,
            'version': table.version,
        }