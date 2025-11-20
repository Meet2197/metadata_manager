# search/management/commands/reindex_search.py
from django.core.management.base import BaseCommand
from search.indexer import SearchIndexer
from core.models.entities import Table, Database, Schema
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reindex all entities in Elasticsearch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--entity-type',
            type=str,
            choices=['table', 'database', 'schema', 'all'],
            default='all',
            help='Entity type to reindex',
        )

    def handle(self, *args, **options):
        indexer = SearchIndexer()
        entity_type = options['entity_type']
        
        if entity_type in ['table', 'all']:
            self.reindex_tables(indexer)
            
        if entity_type in ['database', 'all']:
            self.reindex_databases(indexer)
            
        if entity_type in ['schema', 'all']:
            self.reindex_schemas(indexer)

    def reindex_tables(self, indexer):
        self.stdout.write('Reindexing tables...')
        tables = Table.objects.filter(deleted=False)
        
        for table in tables:
            try:
                indexer.index_entity(table)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error indexing {table.name}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully reindexed {tables.count()} tables')
        )

    def reindex_databases(self, indexer):
        self.stdout.write('Reindexing databases...')
        databases = Database.objects.filter(deleted=False)
        
        for database in databases:
            try:
                indexer.index_entity(database)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error indexing {database.name}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully reindexed {databases.count()} databases')
        )

    def reindex_schemas(self, indexer):
        self.stdout.write('Reindexing schemas...')
        schemas = Schema.objects.filter(deleted=False)
        
        for schema in schemas:
            try:
                indexer.index_entity(schema)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error indexing {schema.name}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully reindexed {schemas.count()} schemas')
        )