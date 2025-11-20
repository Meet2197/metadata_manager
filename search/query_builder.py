# search/query_builder.py
from typing import List, Dict, Optional


class QueryBuilder:
    """Builder for Elasticsearch queries"""
    
    def build_search_query(self, query: str, entity_types: List[str] = None,
                          filters: Dict = None) -> Dict:
        """Build search query"""
        must_clauses = []
        filter_clauses = []
        
        # Text search
        if query:
            must_clauses.append({
                'multi_match': {
                    'query': query,
                    'fields': [
                        'name^3',
                        'display_name^2',
                        'description',
                        'fully_qualified_name',
                        'columns.name',
                        'columns.description'
                    ],
                    'fuzziness': 'AUTO'
                }
            })
            
        # Entity type filter
        if entity_types:
            filter_clauses.append({
                'terms': {'entity_type': entity_types}
            })
            
        # Additional filters
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    filter_clauses.append({'terms': {field: value}})
                else:
                    filter_clauses.append({'term': {field: value}})
                    
        # Build query
        query_body = {
            'query': {
                'bool': {
                    'must': must_clauses,
                    'filter': filter_clauses
                }
            },
            'highlight': {
                'fields': {
                    'name': {},
                    'description': {},
                    'columns.name': {},
                    'columns.description': {}
                }
            }
        }
        
        return query_body
        
    def build_aggregation_query(self, field: str, entity_type: str = None) -> Dict:
        """Build aggregation query"""
        query = {
            'size': 0,
            'aggs': {
                f'{field}_agg': {
                    'terms': {
                        'field': field,
                        'size': 100
                    }
                }
            }
        }
        
        if entity_type:
            query['query'] = {
                'term': {'entity_type': entity_type}
            }
            
        return query