# ingestion/framework/sink.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from core.services.metadata_service import MetadataService
import logging

logger = logging.getLogger(__name__)


class Sink(ABC):
    """Abstract base class for sinks"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    @abstractmethod
    def write(self, metadata: Dict) -> bool:
        """Write metadata to sink"""
        pass
        
    @abstractmethod
    def write_batch(self, metadata_list: List[Dict]) -> int:
        """Write batch of metadata to sink"""
        pass


class MetadataStoreSink(Sink):
    """Sink for writing to metadata store (database)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.metadata_service = MetadataService()
        self.batch_size = config.get('batch_size', 100)
        
    def write(self, metadata: Dict) -> bool:
        """Write single metadata entity"""
        try:
            entity_type = metadata.pop('entity_type', 'table')
            
            if entity_type == 'table':
                table = self.metadata_service.create_table(
                    data=metadata,
                    user=self.config.get('user')
                )
                return table is not None
                
            return False
            
        except Exception as e:
            logger.error(f"Error writing metadata: {str(e)}")
            return False
            
    def write_batch(self, metadata_list: List[Dict]) -> int:
        """Write batch of metadata entities"""
        success_count = 0
        
        for metadata in metadata_list:
            if self.write(metadata):
                success_count += 1
                
        logger.info(f"Written {success_count}/{len(metadata_list)} entities")
        return success_count