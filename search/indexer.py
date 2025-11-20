# search/indexer.py
from search.elasticsearch_client import ElasticsearchClient
from core.models.entities import Table, Database, Schema
import logging

logger = logging.getLogger(__name__)


class SearchIndexer:
    """Indexer for metadata entities"""
    
    def __init__(self):
        self.es_client = ElasticsearchClient()
        self._initialize_indices()
        
    def _initialize_indices(self):
        """Initialize Elasticsearch indices"""
        # Table index
        table_mappings = {
            'properties': {
                'entity_type': {'type': 'keyword'},
                'name': {
                    'type': 'text',
                    'fields': {'keyword': {'type': 'keyword'}}
                },
                'fully_qualified_name': {'type': 'keyword'},
                'display_name': {
                    'type': 'text',
                    'fields': {'keyword': {'type': 'keyword'}}
                },
                'description': {'type': 'text'},
                'table_type': {'type': 'keyword'},
                'database': {'type': 'keyword'},
                # search/indexer.py (continued)
                'schema': {'type': 'keyword'},
                'owner': {'type': 'keyword'},
                'tags': {'type': 'keyword'},
                'columns': {
                    'type': 'nested',
                    'properties': {
                        'name': {'type': 'text'},
                        'data_type': {'type': 'keyword'},
                        'description': {'type': 'text'}
                    }
                },
                'created_at': {'type': 'date'},
                'updated_at': {'type': 'date'},
            }
        }
        
        self.es_client.create_index('table', table_mappings)
        
    def index_entity(self, entity: Any):
        """Index an entity"""
        try:
            if isinstance(entity, Table):
                self._index_table(entity)
            elif isinstance(entity, Database):
                self._index_database(entity)
            elif isinstance(entity, Schema):
                self._index_schema(entity)
            else:
                logger.warning(f"Unsupported entity type: {type(entity)}")
                
        except Exception as e:
            logger.error(f"Error indexing entity: {str(e)}")
            raise
            
    def _index_table(self, table: Table):
        """Index a table entity"""
        document = {
            'id': str(table.id),
            'entity_type': 'table',
            'name': table.name,
            'fully_qualified_name': table.fully_qualified_name,
            'display_name': table.display_name,
            'description': table.description,
            'table_type': table.table_type,
            'database': table.database.name,
            'schema': table.schema.name,
            'owner': table.owner.display_name if table.owner else None,
            'tags': [tag.name for tag in table.tags.all()],
            'columns': table.columns,
            'created_at': table.created_at.isoformat(),
            'updated_at': table.updated_at.isoformat(),
        }
        
        self.es_client.index_document('table', str(table.id), document)
        
    def _index_database(self, database: Database):
        """Index a database entity"""
        document = {
            'id': str(database.id),
            'entity_type': 'database',
            'name': database.name,
            'fully_qualified_name': database.fully_qualified_name,
            'display_name': database.display_name,
            'description': database.description,
            'data_source': database.data_source.name,
            'owner': database.owner.display_name if database.owner else None,
            'tags': [tag.name for tag in database.tags.all()],
            'created_at': database.created_at.isoformat(),
            'updated_at': database.updated_at.isoformat(),
        }
        
        self.es_client.index_document('database', str(database.id), document)
        
    def _index_schema(self, schema: Schema):
        """Index a schema entity"""
        document = {
            'id': str(schema.id),
            'entity_type': 'schema',
            'name': schema.name,
            'fully_qualified_name': schema.fully_qualified_name,
            'display_name': schema.display_name,
            'description': schema.description,
            'database': schema.database.name,
            'created_at': schema.created_at.isoformat(),
            'updated_at': schema.updated_at.isoformat(),
        }
        
        self.es_client.index_document('schema', str(schema.id), document)
        
    def update_entity(self, entity: Any):
        """Update indexed entity"""
        self.index_entity(entity)  # Elasticsearch will update if exists
        
    def delete_entity(self, entity_id: str):
        """Delete entity from index"""
        self.es_client.delete_document('table', entity_id)
        
    def bulk_index_entities(self, entities: list):
        """Bulk index entities"""
        documents = []
        for entity in entities:
            if isinstance(entity, Table):
                documents.append(self._prepare_table_document(entity))
                
        if documents:
            self.es_client.bulk_index('table', documents)
            
    def _prepare_table_document(self, table: Table) -> dict:
        """Prepare table document for indexing"""
        return {
            'id': str(table.id),
            'entity_type': 'table',
            'name': table.name,
            'fully_qualified_name': table.fully_qualified_name,
            'display_name': table.display_name,
            'description': table.description,
            'table_type': table.table_type,
            'database': table.database.name,
            'schema': table.schema.name,
            'columns': table.columns,
        }