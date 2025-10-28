"""
Configuración simplificada usando python-dotenv
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno desde .env
load_dotenv()

def get_artemis_config():
    """Configuración de Artemis"""
    return {
        'host': os.getenv('ARTEMIS_HOST', 'localhost'),
        'port': int(os.getenv('ARTEMIS_PORT', '61616')),
        'username': os.getenv('ARTEMIS_USERNAME', 'artemis'),
        'password': os.getenv('ARTEMIS_PASSWORD', 'artemis'),
        'virtual_host': os.getenv('ARTEMIS_VIRTUAL_HOST', '/'),
        'queue_document_processing': os.getenv('ARTEMIS_QUEUE', 'test'),
        'max_reconnect_attempts': int(os.getenv('ARTEMIS_MAX_RECONNECT_ATTEMPTS', '10')),
        'reconnect_delay': int(os.getenv('ARTEMIS_RECONNECT_DELAY', '5')),
        'connection_timeout': int(os.getenv('ARTEMIS_CONNECTION_TIMEOUT', '30'))
    }

def get_sftp_config():
    """Configuración de SFTP"""
    return {
        'hostname': os.getenv('SFTP_HOSTNAME', 'localhost'),
        'port': int(os.getenv('SFTP_PORT', '22')),
        'username': os.getenv('SFTP_USERNAME', 'user'),
        'password': os.getenv('SFTP_PASSWORD', 'password'),
        'remote_input_path': os.getenv('SFTP_REMOTE_PATH', '/'),
        'timeout': int(os.getenv('SFTP_TIMEOUT', '30')),
        'max_retries': int(os.getenv('SFTP_MAX_RETRIES', '3')), 
        'local_load_directory': os.getenv('SFTP_LOAD_DIRECTORY', '/documentos_download')
    }

def get_elasticsearch_config():
    """Configuración de Elasticsearch"""
    return {
        'host': os.getenv('ELASTICSEARCH_HOST', 'localhost'),
        'port': int(os.getenv('ELASTICSEARCH_PORT', '9200')),
        'scheme': os.getenv('ELASTICSEARCH_SCHEME', 'http'),
        'username': os.getenv('ELASTICSEARCH_USERNAME', 'elastic'),
        'password': os.getenv('ELASTICSEARCH_PASSWORD', 'elastic'),
        'timeout': int(os.getenv('ELASTICSEARCH_TIMEOUT', '30')),
        'index_name': os.getenv('ELASTICSEARCH_INDEX_NAME', 'index_documents'),
        'verify_certs': os.getenv('ELASTICSEARCH_VERIFY_CERTS', 'false').lower() == 'true',
        'ssl_show_warn': os.getenv('ELASTICSEARCH_SSL_SHOW_WARN', 'false').lower() == 'true',
        'ca_cert_path': os.getenv('ELASTICSEARCH_CA_CERT_PATH', None)
    }

def get_text_splitter_config():
    """Configuración del fragmentador de texto"""
    return {
        'chunk_size': int(os.getenv('TEXT_CHUNK_SIZE', '1000')),
        'chunk_overlap': int(os.getenv('TEXT_CHUNK_OVERLAP', '200'))
    }

def get_vectorization_config():
    """Configuración de vectorización"""
    return {
        'model_name': os.getenv('VECTORIZATION_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2'),
        'device': os.getenv('VECTORIZATION_DEVICE', 'cpu'),
        'batch_size': int(os.getenv('VECTORIZATION_BATCH_SIZE', '32'))
    }

def get_logging_config():
    """Configuración de logging"""
    return {
        'level': os.getenv('LOG_LEVEL', 'INFO'),
        'format': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    }

def get_text_converter_config():
    """Obtener tipos de archivo soportados"""
    types = os.getenv('SUPPORTED_FILE_TYPES', '.pdf,.docx,.txt')
    return {
        'supported_types': [t.strip() for t in types.split(',') if t.strip()]
    }