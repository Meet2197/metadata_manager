# api/v1/views/search_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.services.search_service import SearchService
import logging

logger = logging.getLogger(__name__)


class SearchView(APIView):
    """Universal search endpoint"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = SearchService()
    
    def get(self, request):
        """Search entities"""
        query = request.query_params.get('q', '')
        entity_types = request.query_params.getlist('type')
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 10))
        
        # Extract filters
        filters = {}
        for key, value in request.query_params.items():
            if key not in ['q', 'type', 'page', 'size']:
                filters[key] = value
        
        try:
            results = self.search_service.search(
                query=query,
                entity_types=entity_types or None,
                filters=filters if filters else None,
                page=page,
                size=size
            )
            
            return Response(results)
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=400
            )


class SuggestView(APIView):
    """Search suggestions endpoint"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = SearchService()
    
    def get(self, request):
        """Get search suggestions"""
        query = request.query_params.get('q', '')
        field = request.query_params.get('field', 'name')
        
        try:
            suggestions = self.search_service.suggest(query, field)
            return Response({'suggestions': suggestions})
            
        except Exception as e:
            logger.error(f"Suggestion error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=400
            )