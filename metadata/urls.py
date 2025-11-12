# metadata/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Data Sources
    path('sources/', views.data_source_list, name='data_source_list'),
    path('sources/<int:pk>/', views.data_source_detail, name='data_source_detail'),
    path('sources/create/', views.data_source_create, name='data_source_create'),
    path('sources/<int:pk>/update/', views.data_source_update, name='data_source_update'),
    
    # Tables
    path('tables/', views.table_list, name='table_list'),
    path('tables/<int:pk>/', views.table_detail, name='table_detail'),
    path('tables/create/', views.table_create, name='table_create'),
    path('tables/<int:pk>/update/', views.table_update, name='table_update'),
    
    # Lineage
    path('lineage/', views.lineage_view, name='lineage_view'),
    
    # Glossary
    path('glossary/', views.glossary_list, name='glossary_list'),
    
    # API
    path('api/search/tables/', views.api_search_tables, name='api_search_tables'),
]