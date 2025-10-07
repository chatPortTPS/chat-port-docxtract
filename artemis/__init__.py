"""
Módulo Artemis para Document Extractor
======================================

Módulo principal para la integración con Apache ActiveMQ Artemis.

Componentes principales:
- ArtemisConnector: Conector principal para recibir mensajes JSON

Uso básico:
    from artemis import ArtemisConnector
    
    connector = ArtemisConnector()
    connector.connect()
    connector.subscribe_to_queue("mi.cola", mi_handler)
    connector.start_listening()
"""

from .connector import ArtemisConnector, ArtemisMessageListener
from .config_ar import load_config

__version__ = "1.0.0"
__author__ = "Document Extractor Team"

__all__ = [
    'ArtemisConnector',
    'ArtemisMessageListener', 
    'load_config'
]
