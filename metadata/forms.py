# metadata/forms.py
from django import forms
from .models import DataSource, Schema, Table, Column, DataLineage, Glossary, DataQualityRule
from django import forms
from .models import DataSource


class DataSourceUploadForm(forms.ModelForm):
    # Overwrite the default FileField to make it non-required initially 
    # if you want to allow creating a DataSource without a file (e.g., manual entry)
    uploaded_file = forms.FileField(
        label='Upload Data Source File',
        help_text='Supported: JSON, CSV, TXT, Excel, XML, RDF, MARC, METS, TEI, etc.'
    )
    
    class Meta:
        model = DataSource
        fields = ['name', 'description', 'uploaded_file']

class DataSourceForm(forms.ModelForm):
    class Meta:
        model = DataSource
        # Fields that are CAUSING THE CRASH are removed below:
        # fields = ['name', 'description', 'source_type', 'host', 'port', 
        #           'database_name', 'username', 'password', 'is_active']
        
        # New, temporary fields list to resolve the crash:
        fields = ['name', 'description']
        
        widgets = {
            # Removed 'password' widget as the field is gone
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ['name', 'schema', 'description', 'table_type', 'tags', 'owner']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ColumnForm(forms.ModelForm):
    class Meta:
        model = Column
        fields = ['name', 'table', 'data_type', 'description', 'is_primary_key', 
                  'is_foreign_key', 'is_nullable', 'default_value', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class DataLineageForm(forms.ModelForm):
    class Meta:
        model = DataLineage
        fields = ['source_table', 'target_table', 'lineage_type', 'description', 
                  'transformation_logic']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'transformation_logic': forms.Textarea(attrs={'rows': 4}),
        }


class GlossaryForm(forms.ModelForm):
    class Meta:
        model = Glossary
        fields = ['term', 'definition', 'category', 'related_terms', 'owner']
        widgets = {
            'definition': forms.Textarea(attrs={'rows': 4}),
        }


class DataQualityRuleForm(forms.ModelForm):
    class Meta:
        model = DataQualityRule
        fields = ['name', 'table', 'column', 'rule_type', 'rule_definition', 'is_active']
        widgets = {
            'rule_definition': forms.Textarea(attrs={'rows': 4}),
        }