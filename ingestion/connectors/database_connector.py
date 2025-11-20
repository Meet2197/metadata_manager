# ingestion/connectors/database_connector.py
from ingestion.framework.source import Source
from typing import Iterator, Dict
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, inspect
import logging

logger = logging.getLogger(__name__)


class DatabaseConnector(Source):
    """Connector for database sources (MySQL, PostgreSQL, etc.)"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.engine = None
        self.inspector = None
        
    def connect(self) -> bool:
        """Connect to database"""
        try:
            connection_string = self._build_connection_string()
            self.engine = create_engine(connection_string)
            self.inspector = inspect(self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
                
            logger.info(f"Connected to database: {self.config.get('database')}")
            return True
            
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            return False
            
    def disconnect(self):
        """Disconnect from database"""
        if self.engine:
            self.engine.dispose()
            logger.info("Disconnected from database")
            
    def get_metadata(self) -> Iterator[Dict]:
        """Get metadata from database"""
        if not self.inspector:
            raise RuntimeError("Not connected to database")
            
        database_name = self.config.get('database')
        
        # Get all schemas
        schemas = self.inspector.get_schema_names()
        
        for schema in schemas:
            # Skip system schemas
            if self._should_skip_schema(schema):
                continue
                
            # Get tables in schema
            tables = self.inspector.get_table_names(schema=schema)
            
            for table_name in tables:
                yield self._get_table_metadata(schema, table_name, database_name)
                
    def _get_table_metadata(self, schema: str, table_name: str, database: str) -> Dict:
        """Get metadata for a specific table"""
        # Get columns
        columns = self.inspector.get_columns(table_name, schema=schema)
        
        # Get primary keys
        pk_constraint = self.inspector.get_pk_constraint(table_name, schema=schema)
        pk_columns = pk_constraint.get('constrained_columns', [])
        
        # Get foreign keys
        fk_constraints = self.inspector.get_foreign_keys(table_name, schema=schema)
        fk_columns = [fk['constrained_columns'][0] for fk in fk_constraints if fk['constrained_columns']]
        
        # Transform columns
        transformed_columns = []
        for idx, col in enumerate(columns):
            transformed_columns.append({
                'name': col['name'],
                'data_type': str(col['type']),
                'ordinal_position': idx + 1,
                'is_nullable': col['nullable'],
                'is_primary_key': col['name'] in pk_columns,
                'is_foreign_key': col['name'] in fk_columns,
                'default_value': str(col.get('default', '')),
            })
            
        return {
            'entity_type': 'table',
            'name': table_name,
            'database': database,
            'schema': schema,
            'fully_qualified_name': f"{database}.{schema}.{table_name}",
            'display_name': table_name,
            'table_type': 'Regular',
            'columns': transformed_columns,
            'source_type': self.config.get('source_type', 'mysql'),
        }
        
    def _build_connection_string(self) -> str:
        """Build database connection string"""
        db_type = self.config.get('source_type', 'mysql')
        host = self.config.get('host', 'localhost')
        port = self.config.get('port', 3306)
        database = self.config.get('database')
        username = self.config.get('username')
        password = self.config.get('password')
        
        if db_type == 'mysql':
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == 'postgresql':
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
            
    def _should_skip_schema(self, schema: str) -> bool:
        """Check if schema should be skipped"""
        skip_schemas = ['information_schema', 'mysql', 'performance_schema', 'sys', 'pg_catalog']
        return schema.lower() in skip_schemas