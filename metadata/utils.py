# metadata/utils.py
import pandas as pd
import json
import rdflib
from lxml import etree
import os
import io

def parse_xml_metadata(file_content, schema_type="Generic"):
    """
    A unified parser for XML-based schemas (DC, DataCite, MARC, METS, TEI, etc.).
    Uses lxml's robust parsing and returns key/value pairs.
    """
    metadata = {"schema_type": schema_type}
    try:
        # Use defusedxml/etree if preferred for security, or standard lxml
        root = etree.parse(io.BytesIO(file_content)).getroot()
        
        # Simple extraction: iterate over all unique tag names and their first text value
        for el in root.iter():
            # Clean up namespaces and ignore comments/processing instructions
            tag = etree.QName(el).localname
            if tag and el.text and el.text.strip() and tag not in metadata:
                metadata[tag] = el.text.strip()
                
        # Add a count of all elements for lineage tracking
        metadata['total_elements'] = len(list(root.iter()))
        
    except Exception as e:
        metadata["error"] = f"XML Parsing Error: {e}"
    return metadata

def parse_tabular_metadata(file_content, extension):
    """Parses CSV, TXT (as CSV), and Excel formats using pandas."""
    try:
        if extension in ['csv', 'txt']:
            df = pd.read_csv(io.StringIO(file_content.decode('utf-8')))
            return {
                "file_type": "Tabular/CSV",
                "column_names": df.columns.tolist(),
                "row_count": len(df)
            }
        elif extension in ['xlsx', 'xls']:
            # Read all sheets from Excel
            xls = pd.ExcelFile(io.BytesIO(file_content))
            metadata = {"file_type": "Excel", "sheets": {}}
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name)
                metadata['sheets'][sheet_name] = {
                    "column_names": df.columns.tolist(),
                    "row_count": len(df)
                }
            return metadata
            
    except Exception as e:
        return {"error": f"Tabular Parsing Error: {e}"}

def parse_file_metadata(uploaded_file):
    """The main routing function to process the file based on extension."""
    file_name = uploaded_file.name
    extension = os.path.splitext(file_name)[-1].lower().strip('.')
    
    # Read file content into memory (safe for temporary processing)
    file_content = uploaded_file.read() 
    
    # --- JSON / Text ---
    if extension == 'json':
        try:
            return {"file_type": "JSON", "extracted_data": json.loads(file_content.decode('utf-8'))}
        except Exception as e:
            return {"error": f"JSON Parsing Error: {e}"}
            
    # --- Tabular (CSV, TXT, Excel) ---
    elif extension in ['csv', 'txt', 'xlsx', 'xls']:
        return parse_tabular_metadata(file_content, extension)

    # --- RDF (Resource Description Framework) ---
    elif extension in ['rdf', 'ttl', 'nt']:
        try:
            g = rdflib.Graph()
            # Try to guess the format (xml, turtle, ntriples)
            g.parse(data=file_content.decode('utf-8'), format='guess')
            return {
                "file_type": "RDF",
                "triples_count": len(g),
                "namespaces": [str(n) for n in g.namespaces()]
            }
        except Exception as e:
            return {"error": f"RDF Parsing Error: {e}"}

    # --- XML and XML-based Schemas ---
    elif extension in ['xml', 'marc', 'mets', 'tei', 'mxf', 'pbcore']:
        # Note: This is a generalized parser. For production-level detail, you would
        # implement dedicated schema-specific logic for each of these types (e.g., using python-marc).
        return parse_xml_metadata(file_content, schema_type=extension.upper())

    # --- Fallback ---
    else:
        return {"error": f"Unsupported file type: .{extension}"}