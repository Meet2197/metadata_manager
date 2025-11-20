# core/management/commands/sync_metadata.py
from django.core.management.base import BaseCommand
from ingestion.workflows.workflow_manager import WorkflowManager
from core.models.entities import DataSource
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync metadata from data sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-id',
            type=str,
            help='Specific data source ID to sync',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sync all active data sources',
        )

    def handle(self, *args, **options):
        workflow_manager = WorkflowManager()
        
        if options['source_id']:
            self.sync_source(workflow_manager, options['source_id'])
        elif options['all']:
            self.sync_all_sources(workflow_manager)
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --source-id or --all')
            )

    def sync_source(self, manager, source_id):
        try:
            source = DataSource.objects.get(id=source_id)
            self.stdout.write(f'Syncing {source.name}...')
            
            workflow_config = self._build_workflow_config(source)
            workflow = manager.create_workflow(str(source.id), workflow_config)
            result = manager.execute_workflow(str(source.id))
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully synced {source.name}: {result["stats"]}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error syncing source: {str(e)}')
            )

    def sync_all_sources(self, manager):
        sources = DataSource.objects.filter(is_active=True)
        self.stdout.write(f'Found {sources.count()} active sources')
        
        for source in sources:
            self.sync_source(manager, str(source.id))

    def _build_workflow_config(self, source):
        return {
            'source': {
                'type': source.source_type,
                **source.connection_config
            },
            'processors': [
                {'type': 'transformation'},
                {'type': 'enrichment'}
            ],
            'sink': {
                'type': 'metadata_store'
            }
        }