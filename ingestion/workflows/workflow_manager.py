# ingestion/workflows/workflow_manager.py
from typing import Dict, List, Any
from ingestion.framework.source import Source
from ingestion.framework.processor import Processor
from ingestion.framework.sink import Sink
from ingestion.connectors.database_connector import DatabaseConnector
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manager for ingestion workflows"""
    
    def __init__(self):
        self.workflows = {}
        
    def create_workflow(self, workflow_id: str, config: Dict) -> Dict:
        """Create a new ingestion workflow"""
        workflow = {
            'id': workflow_id,
            'config': config,
            'status': 'created',
            'source': self._create_source(config.get('source')),
            'processors': self._create_processors(config.get('processors', [])),
            'sink': self._create_sink(config.get('sink')),
        }
        
        self.workflows[workflow_id] = workflow
        return workflow
        
    def execute_workflow(self, workflow_id: str) -> Dict:
        """Execute ingestion workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
            
        try:
            workflow['status'] = 'running'
            
            source = workflow['source']
            processors = workflow['processors']
            sink = workflow['sink']
            
            # Pull metadata from source
            with source:
                metadata_count = 0
                success_count = 0
                error_count = 0
                
                for metadata in source.get_metadata():
                    try:
                        # Process metadata through processors
                        processed_metadata = metadata
                        for processor in processors:
                            processed_metadata = processor.process(processed_metadata)
                            
                        # Write to sink
                        if sink.write(processed_metadata):
                            success_count += 1
                        else:
                            error_count += 1
                            
                        metadata_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing metadata: {str(e)}")
                        error_count += 1
                        
            workflow['status'] = 'completed'
            workflow['stats'] = {
                'total': metadata_count,
                'success': success_count,
                'errors': error_count
            }
            
            logger.info(f"Workflow {workflow_id} completed: {workflow['stats']}")
            return workflow
            
        except Exception as e:
            workflow['status'] = 'failed'
            workflow['error'] = str(e)
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            raise
            
    def _create_source(self, config: Dict) -> Source:
        """Create source based on config"""
        source_type = config.get('type')
        
        if source_type in ['mysql', 'postgresql']:
            return DatabaseConnector(config)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
            
    def _create_processors(self, configs: List[Dict]) -> List[Processor]:
        """Create processors based on configs"""
        from ingestion.framework.processor import EnrichmentProcessor, TransformationProcessor
        
        processors = []
        for config in configs:
            processor_type = config.get('type')
            
            if processor_type == 'enrichment':
                processors.append(EnrichmentProcessor(config))
            elif processor_type == 'transformation':
                processors.append(TransformationProcessor(config))
                
        return processors
        
    def _create_sink(self, config: Dict) -> Sink:
        """Create sink based on config"""
        from ingestion.framework.sink import MetadataStoreSink
        
        sink_type = config.get('type', 'metadata_store')
        
        if sink_type == 'metadata_store':
            return MetadataStoreSink(config)
        else:
            raise ValueError(f"Unsupported sink type: {sink_type}")


@shared_task
def execute_workflow_task(workflow_id: str):
    """Celery task for executing workflow"""
    manager = WorkflowManager()
    return manager.execute_workflow(workflow_id)