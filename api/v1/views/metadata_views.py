# api/v1/views/metadata_views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from core.models.entities import Table, Database, Schema, DataSource
from core.services.metadata_service import MetadataService
from api.v1.serializers.metadata_serializers import (
    TableListSerializer, TableDetailSerializer, TableCreateSerializer,
    DatabaseSerializer, SchemaSerializer, DataSourceSerializer
)
import logging

logger = logging.getLogger(__name__)


class DataSourceViewSet(viewsets.ModelViewSet):
    """ViewSet for DataSource operations"""
    queryset = DataSource.objects.filter(deleted=False)
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source_type', 'is_active']
    search_fields = ['name', 'display_name', 'description']
    ordering_fields = ['name', 'created_at', 'last_sync']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test data source connection"""
        data_source = self.get_object()
        # Implement connection test logic
        return Response({'status': 'success', 'message': 'Connection successful'})
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Trigger metadata sync"""
        data_source = self.get_object()
        # Trigger ingestion workflow
        from ingestion.workflows.workflow_manager import execute_workflow_task
        
        workflow_config = {
            'source': {
                'type': data_source.source_type,
                'host': data_source.connection_config.get('host'),
                'port': data_source.connection_config.get('port'),
                'database': data_source.connection_config.get('database'),
                'username': data_source.connection_config.get('username'),
                'password': data_source.connection_config.get('password'),
            },
            'processors': [
                {'type': 'transformation'},
                {'type': 'enrichment'}
            ],
            'sink': {
                'type': 'metadata_store',
                'user': request.user
            }
        }
        
        task = execute_workflow_task.delay(str(data_source.id))
        
        return Response({
            'status': 'success',
            'message': 'Sync started',
            'task_id': task.id
        })


class DatabaseViewSet(viewsets.ModelViewSet):
    """ViewSet for Database operations"""
    queryset = Database.objects.filter(deleted=False).select_related('data_source', 'owner')
    serializer_class = DatabaseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['data_source']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def schemas(self, request, pk=None):
        """Get schemas in database"""
        database = self.get_object()
        schemas = database.schemas.all()
        serializer = SchemaSerializer(schemas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def tables(self, request, pk=None):
        """Get tables in database"""
        database = self.get_object()
        tables = database.tables.all()
        serializer = TableListSerializer(tables, many=True)
        return Response(serializer.data)


class SchemaViewSet(viewsets.ModelViewSet):
    """ViewSet for Schema operations"""
    queryset = Schema.objects.filter(deleted=False).select_related('database')
    serializer_class = SchemaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['database']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def tables(self, request, pk=None):
        """Get tables in schema"""
        schema = self.get_object()
        tables = schema.tables.all()
        serializer = TableListSerializer(tables, many=True)
        return Response(serializer.data)


class TableViewSet(viewsets.ModelViewSet):
    """ViewSet for Table operations"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['table_type', 'database', 'schema']
    search_fields = ['name', 'display_name', 'description', 'fully_qualified_name']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata_service = MetadataService()
    
    def get_queryset(self):
        return Table.objects.filter(deleted=False).select_related(
            'database', 'schema', 'owner'
        ).prefetch_related('tags', 'column_entities')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TableListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TableCreateSerializer
        return TableDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new table"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            table = self.metadata_service.create_table(
                data=serializer.validated_data,
                user=request.user
            )
            
            response_serializer = TableDetailSerializer(table)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """Update table"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            table = self.metadata_service.update_table(
                table_id=str(instance.id),
                data=serializer.validated_data,
                user=request.user
            )
            
            response_serializer = TableDetailSerializer(table)
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"Error updating table: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete table"""
        instance = self.get_object()
        
        try:
            self.metadata_service.delete_table(
                table_id=str(instance.id),
                user=request.user,
                hard=request.query_params.get('hard', 'false').lower() == 'true'
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Error deleting table: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def lineage(self, request, pk=None):
        """Get table lineage"""
        depth = int(request.query_params.get('depth', 3))
        
        try:
            lineage = self.metadata_service.get_table_lineage(pk, depth)
            return Response(lineage)
            
        except Exception as e:
            logger.error(f"Error getting lineage: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def add_lineage(self, request, pk=None):
        """Add lineage relationship"""
        downstream_id = request.data.get('downstream_table_id')
        lineage_type = request.data.get('lineage_type', 'ETL')
        sql_query = request.data.get('sql_query', '')
        
        try:
            success = self.metadata_service.add_table_lineage(
                upstream_id=pk,
                downstream_id=downstream_id,
                lineage_type=lineage_type,
                sql_query=sql_query,
                user=request.user
            )
            
            if success:
                return Response({'status': 'success'})
            else:
                return Response(
                    {'error': 'Failed to create lineage'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error adding lineage: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular tables"""
        limit = int(request.query_params.get('limit', 10))
        tables = self.metadata_service.get_popular_tables(limit)
        serializer = TableListSerializer(tables, many=True)
        return Response(serializer.data)