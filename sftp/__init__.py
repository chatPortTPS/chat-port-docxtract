"""
Módulo SFTP para Document Extractor
===================================

Módulo principal para la integración con servidores SFTP.

Componentes principales:
- SftpConnector: Conector principal para transferencias SFTP
- config_utils: Utilidades de configuración
- examples: Ejemplos de uso

Uso básico:
    from sftp import SftpConnector
    
    connector = SftpConnector()
    connector.connect()
    connector.download_file("file.pdf")
    connector.disconnect()
"""

from .connector import SftpConnector
from .config_sftp import load_config

__version__ = "1.0.0"
__author__ = "Document Extractor Team"

__all__ = [
    'SftpConnector',
    'load_config'
]
