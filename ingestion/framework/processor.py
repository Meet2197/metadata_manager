# ingestion/framework/processor.py
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class Processor(ABC):
    """Abstract base class for processors"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
    @abstractmethod
    def process(self, metadata: Dict) -> Dict:
        """Process metadata"""
        pass
        
    def validate(self, metadata: Dict) -> bool:
        """Validate metadata"""
        return True


class EnrichmentProcessor(Processor):
    """Processor for enriching metadata"""
    
    def process(self, metadata: Dict) -> Dict:
        """Add enrichment to metadata"""
        # Add tags
        metadata['tags'] = self._infer_tags(metadata)
        
        # Add owner
        metadata['owner'] = self._infer_owner(metadata)
        
        # Add descriptions
        if not metadata.get('description'):
            metadata['description'] = self._generate_description(metadata)
            
        return metadata
        
    def _infer_tags(self, metadata: Dict) -> list:
        """Infer tags based on metadata"""
        tags = []
        
        # Tag based on name patterns
        name = metadata.get('name', '').lower()
        if 'temp' in name or 'tmp' in name:
            tags.append('temporary')
        if 'staging' in name or 'stg' in name:
            tags.append('staging')
        if 'prod' in name or 'production' in name:
            tags.append('production')
            
        return tags
        
    def _infer_owner(self, metadata: Dict) -> str:
        """Infer owner based on metadata"""
        # Implementation for owner inference
        return metadata.get('owner', 'unknown')
        
    def _generate_description(self, metadata: Dict) -> str:
        """Generate description based on metadata"""
        name = metadata.get('name', '')
        table_type = metadata.get('table_type', 'table')
        return f"Auto-generated: {table_type} {name}"


class TransformationProcessor(Processor):
    """Processor for transforming metadata"""
    
    def process(self, metadata: Dict) -> Dict:
        """Transform metadata format"""
        transformed = {
            'name': metadata.get('table_name') or metadata.get('name'),
            'fully_qualified_name': self._build_fqn(metadata),
            'display_name': metadata.get('display_name') or metadata.get('name'),
            'description': metadata.get('description', ''),
            'table_type': metadata.get('type', 'Regular'),
            'columns': self._transform_columns(metadata.get('columns', [])),
        }
        return transformed
        
    def _build_fqn(self, metadata: Dict) -> str:
        """Build fully qualified name"""
        parts = [
            metadata.get('database'),
            metadata.get('schema'),
            metadata.get('table_name') or metadata.get('name')
        ]
        return '.'.join([p for p in parts if p])
        
    def _transform_columns(self, columns: list) -> list:
        """Transform column definitions"""
        return [
            {
                'name': col.get('column_name') or col.get('name'),
                'data_type': col.get('data_type'),
                'ordinal_position': col.get('ordinal_position', 0),
                'is_nullable': col.get('is_nullable', True),
                'description': col.get('description', ''),
            }
            for col in columns
        ]