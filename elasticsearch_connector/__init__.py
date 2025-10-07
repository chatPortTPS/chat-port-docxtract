"""
Módulo Elasticsearch Simple para Document Extractor
===================================================

Módulo simplificado que solo se enfoca en guardar documentos
en un índice de Elasticsearch configurado.

Uso básico:
    from elasticsearch import ElasticsearchConnector
    
    with ElasticsearchConnector() as es:
        # Crear índice si no existe
        es.create_index_if_not_exists(mapping_dict)
        
        # Guardar documento
        document = {
            'document_id': 'doc_001',
            'filename': 'ejemplo.pdf',
            'content': 'Contenido del documento...',
            'status': 'processed'
        }
        es.save_document('doc_001', document)
"""

from .connector import ElasticsearchConnector
from .config_es import load_config, get_connection_params

__all__ = [
    'ElasticsearchConnector',
    'load_config',
    'get_connection_params'
]

__version__ = '1.0.0'
