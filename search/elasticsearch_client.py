# search/elasticsearch_client.py
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Client for Elasticsearch operations"""
    
    def __init__(self):
        self.client = Elasticsearch([settings.ELASTICSEARCH_URL])
        self.index_prefix = 'metadata'
        
    def create_index(self, index_name: str, mappings: dict):
        """Create index with mappings"""
        try:
            full_index_name = f"{self.index_prefix}_{index_name}"
            
            if not self.client.indices.exists(index=full_index_name):
                self.client.indices.create(
                    index=full_index_name,
                    body={'mappings': mappings}
                )
                logger.info(f"Created index: {full_index_name}")
                
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            raise
            
    def index_document(self, index_name: str, doc_id: str, document: dict):
        """Index a single document"""
        try:
            full_index_name = f"{self.index_prefix}_{index_name}"
            self.client.index(
                index=full_index_name,
                id=doc_id,
                body=document
            )
            logger.debug(f"Indexed document: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            raise
            
    def bulk_index(self, index_name: str, documents: list):
        """Bulk index documents"""
        try:
            full_index_name = f"{self.index_prefix}_{index_name}"
            actions = [
                {
                    '_index': full_index_name,
                    '_id': doc['id'],
                    '_source': doc
                }
                for doc in documents
            ]
            
            success, _ = bulk(self.client, actions)
            logger.info(f"Bulk indexed {success} documents")
            return success
            
        except Exception as e:
            logger.error(f"Error bulk indexing: {str(e)}")
            raise
            
    def search(self, query: dict, from_: int = 0, size: int = 10):
        """Search documents"""
        try:
            result = self.client.search(
                index=f"{self.index_prefix}_*",
                body=query,
                from_=from_,
                size=size
            )
            return result
            
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            raise
            
    def suggest(self, query: str, field: str):
        """Get suggestions"""
        try:
            body = {
                'suggest': {
                    'text': query,
                    'completion': {
                        'field': field,
                        'fuzzy': {
                            'fuzziness': 'AUTO'
                        }
                    }
                }
            }
            
            result = self.client.search(
                index=f"{self.index_prefix}_*",
                body=body
            )
            
            return result.get('suggest', {}).get('completion', [])
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return []
            
    def delete_document(self, index_name: str, doc_id: str):
        """Delete a document"""
        try:
            full_index_name = f"{self.index_prefix}_{index_name}"
            self.client.delete(index=full_index_name, id=doc_id)
            logger.debug(f"Deleted document: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise