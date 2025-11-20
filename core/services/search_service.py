# core/services/search_service.py (continued)
from typing import List, Dict, Any
from search.elasticsearch_client import ElasticsearchClient
from search.query_builder import QueryBuilder
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """Service for search operations"""
    
    def __init__(self):
        self.es_client = ElasticsearchClient()
        self.query_builder = QueryBuilder()
        
    def search(self, query: str, entity_types: List[str] = None, 
               filters: Dict = None, page: int = 1, size: int = 10) -> Dict:
        """Universal search across all entity types"""
        try:
            # Build search query
            search_query = self.query_builder.build_search_query(
                query=query,
                entity_types=entity_types or ['table', 'database', 'dashboard'],
                filters=filters
            )
            
            # Execute search
            results = self.es_client.search(
                query=search_query,
                from_=(page - 1) * size,
                size=size
            )
            
            return {
                'total': results['hits']['total']['value'],
                'hits': [self._format_hit(hit) for hit in results['hits']['hits']],
                'aggregations': results.get('aggregations', {}),
                'page': page,
                'size': size
            }
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise
            
    def suggest(self, query: str, field: str = 'name') -> List[str]:
        """Get search suggestions"""
        try:
            suggestions = self.es_client.suggest(query, field)
            return [s['text'] for s in suggestions]
        except Exception as e:
            logger.error(f"Suggestion error: {str(e)}")
            return []
            
    def aggregate(self, field: str, entity_type: str = None) -> Dict:
        """Get aggregations for a field"""
        try:
            query = self.query_builder.build_aggregation_query(field, entity_type)
            results = self.es_client.search(query=query, size=0)
            return results.get('aggregations', {})
        except Exception as e:
            logger.error(f"Aggregation error: {str(e)}")
            return {}
            
    def _format_hit(self, hit: Dict) -> Dict:
        """Format search hit"""
        source = hit['_source']
        return {
            'id': hit['_id'],
            'type': source.get('entity_type'),
            'name': source.get('name'),
            'display_name': source.get('display_name'),
            'description': source.get('description'),
            'fully_qualified_name': source.get('fully_qualified_name'),
            'score': hit['_score'],
            'highlights': hit.get('highlight', {})
        }