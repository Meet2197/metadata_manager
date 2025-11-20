# api/v1/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.v1.views.metadata_views import (
    DataSourceViewSet, DatabaseViewSet, SchemaViewSet, TableViewSet
)
from api.v1.views.search_views import SearchView, SuggestView

router = DefaultRouter()
router.register(r'datasources', DataSourceViewSet, basename='datasource')
router.register(r'databases', DatabaseViewSet, basename='database')
router.register(r'schemas', SchemaViewSet, basename='schema')
router.register(r'tables', TableViewSet, basename='table')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', SearchView.as_view(), name='search'),
    path('suggest/', SuggestView.as_view(), name='suggest'),
]