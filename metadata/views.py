# metadata/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.urls import reverse
from .forms import DataSourceUploadForm
from .models import DataSource
from .utils import parse_file_metadata

from .models import (
    DataSource, Schema, Table, Column, DataLineage, 
    Glossary, DataQualityRule, DataQualityCheck
)
from .forms import (
    DataSourceForm, TableForm, ColumnForm, DataLineageForm, 
    GlossaryForm, DataQualityRuleForm
)
import json

def dashboard(request):
    """Main dashboard view"""
    context = {
        'total_sources': DataSource.objects.count(),
        'total_tables': Table.objects.count(),
        'total_columns': Column.objects.count(),
        'total_lineages': DataLineage.objects.count(),
        'recent_sources': DataSource.objects.all()[:5],
        'recent_tables': Table.objects.select_related('schema__data_source')[:10],
    }
    return render(request, 'dashboard.html', context)

def data_source_upload_view(request):
    if request.method == 'POST':
        form = DataSourceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Save the new DataSource instance (which saves the file to the media path)
            data_source = form.save(commit=False)
            data_source.status = 'PENDING'
            data_source.save()

            try:
                # 2. Process the metadata using the helper function
                processed_data = parse_file_metadata(data_source.uploaded_file)
                
                # 3. Check for errors during processing
                if 'error' in processed_data:
                    data_source.status = 'FAILED'
                else:
                    data_source.status = 'SUCCESS'
                
                # 4. Store the processed metadata and update status
                data_source.processed_metadata = processed_data
                data_source.save()

                # Redirect to the detail page on success
                return redirect(reverse('data_source_detail', args=[data_source.uuid])) 
                
            except Exception as e:
                # Handle any unexpected server errors during processing
                data_source.status = 'FAILED'
                data_source.processed_metadata = {'system_error': str(e)}
                data_source.save()
                # Consider adding a message/logging here

    else:
        form = DataSourceUploadForm()
        
    context = {'form': form}
    # Assumes the URL is mapped to the 'data_sources/form.html' template
    return render(request, 'data_sources/form.html', context)

# Data Source Views
def data_source_list(request):
    """List all data sources"""
    sources = DataSource.objects.annotate(
        schema_count=Count('schemas'),
        table_count=Count('schemas__tables')
    )
    return render(request, 'data_sources/list.html', {'sources': sources})


def data_source_detail(request, pk):
    """Detail view for a data source"""
    source = get_object_or_404(DataSource, pk=pk)
    schemas = source.schemas.annotate(table_count=Count('tables'))
    return render(request, 'data_sources/detail.html', {
        'source': source,
        'schemas': schemas
    })


def data_source_create(request):
    """Create new data source"""
    if request.method == 'POST':
        form = DataSourceForm(request.POST)
        if form.is_valid():
            source = form.save(commit=False)
            if request.user.is_authenticated:
                source.created_by = request.user
            source.save()
            messages.success(request, f'Data source "{source.name}" created successfully!')
            return redirect('data_source_detail', pk=source.pk)
    else:
        form = DataSourceForm()
    return render(request, 'data_sources/form.html', {'form': form, 'action': 'Create'})


def data_source_update(request, pk):
    """Update data source"""
    source = get_object_or_404(DataSource, pk=pk)
    if request.method == 'POST':
        form = DataSourceForm(request.POST, instance=source)
        if form.is_valid():
            form.save()
            messages.success(request, f'Data source "{source.name}" updated successfully!')
            return redirect('data_source_detail', pk=source.pk)
    else:
        form = DataSourceForm(instance=source)
    return render(request, 'data_sources/form.html', {
        'form': form, 
        'action': 'Update', 
        'source': source
    })


# Table Views
def table_list(request):
    """List all tables"""
    tables = Table.objects.select_related('schema__data_source').annotate(
        column_count=Count('columns')
    )
    
    # Search and filter
    search = request.GET.get('search', '')
    source_id = request.GET.get('source', '')
    
    if search:
        tables = tables.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(tags__icontains=search)
        )
    
    if source_id:
        tables = tables.filter(schema__data_source_id=source_id)
    
    sources = DataSource.objects.all()
    
    return render(request, 'tables/list.html', {
        'tables': tables,
        'sources': sources,
        'search': search,
        'selected_source': source_id
    })


def table_detail(request, pk):
    """Detail view for a table"""
    table = get_object_or_404(
        Table.objects.select_related('schema__data_source', 'owner'), 
        pk=pk
    )
    columns = table.columns.all()
    upstream = DataLineage.objects.filter(target_table=table).select_related('source_table')
    downstream = DataLineage.objects.filter(source_table=table).select_related('target_table')
    quality_rules = table.quality_rules.all()
    
    return render(request, 'tables/detail.html', {
        'table': table,
        'columns': columns,
        'upstream': upstream,
        'downstream': downstream,
        'quality_rules': quality_rules
    })


def table_create(request):
    """Create new table"""
    if request.method == 'POST':
        form = TableForm(request.POST)
        if form.is_valid():
            table = form.save()
            messages.success(request, f'Table "{table.name}" created successfully!')
            return redirect('table_detail', pk=table.pk)
    else:
        form = TableForm()
    return render(request, 'tables/form.html', {'form': form, 'action': 'Create'})


def table_update(request, pk):
    """Update table"""
    table = get_object_or_404(Table, pk=pk)
    if request.method == 'POST':
        form = TableForm(request.POST, instance=table)
        if form.is_valid():
            form.save()
            messages.success(request, f'Table "{table.name}" updated successfully!')
            return redirect('table_detail', pk=table.pk)
    else:
        form = TableForm(instance=table)
    return render(request, 'tables/form.html', {
        'form': form, 
        'action': 'Update', 
        'table': table
    })
def data_source_detail_view(request, uuid):
    # Fetch the DataSource object by its UUID
    data_source = get_object_or_404(DataSource, uuid=uuid)
    
    context = {
        'data_source': data_source,
        # The processed metadata is already available as a Python dictionary
        'extracted_metadata': data_source.processed_metadata 
    }
    return render(request, 'data_sources/detail.html', context)

# Lineage Views
def lineage_view(request):
    """Data lineage visualization"""
    tables = Table.objects.select_related('schema__data_source')
    lineages = DataLineage.objects.select_related('source_table', 'target_table')
    
    # Prepare data for visualization
    nodes = []
    links = []
    
    table_dict = {}
    for table in tables:
        node_id = str(table.id)
        table_dict[table.id] = node_id
        nodes.append({
            'id': node_id,
            'name': table.name,
            'schema': table.schema.name,
            'source': table.schema.data_source.name,
            'url': f'/tables/{table.id}/'
        })
    
    for lineage in lineages:
        if lineage.source_table_id in table_dict and lineage.target_table_id in table_dict:
            links.append({
                'source': table_dict[lineage.source_table_id],
                'target': table_dict[lineage.target_table_id],
                'type': lineage.lineage_type
            })
    
    context = {
        'nodes': json.dumps(nodes),
        'links': json.dumps(links),
        'lineages': lineages
    }
    
    return render(request, 'lineage.html', context)


# Glossary Views
def glossary_list(request):
    """List all glossary terms"""
    terms = Glossary.objects.all()
    search = request.GET.get('search', '')
    
    if search:
        terms = terms.filter(
            Q(term__icontains=search) | Q(definition__icontains=search)
        )
    
    return render(request, 'glossary/list.html', {'terms': terms, 'search': search})


# API endpoints for dynamic data
def api_search_tables(request):
    """API endpoint to search tables"""
    query = request.GET.get('q', '')
    tables = Table.objects.filter(name__icontains=query).select_related('schema__data_source')[:10]
    
    results = [{
        'id': t.id,
        'name': t.name,
        'full_name': f"{t.schema.data_source.name}.{t.schema.name}.{t.name}"
    } for t in tables]
    
    return JsonResponse({'results': results})

    