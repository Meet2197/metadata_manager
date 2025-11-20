# ingestion/framework/source.py
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Source(ABC):
    """Abstract base class for data sources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to source"""
        pass
        
    @abstractmethod
    def disconnect(self):
        """Close connection to source"""
        pass
        
    @abstractmethod
    def get_metadata(self) -> Iterator[Dict]:
        """Yield metadata from source"""
        pass
        
    def test_connection(self) -> bool:
        """Test if connection is valid"""
        try:
            return self.connect()
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
            
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()