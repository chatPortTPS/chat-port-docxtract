
from typing import Dict, Any

from config_utils import get_text_converter_config, get_sftp_config

def load_config() -> Dict[str, Any]:
    """
    Carga la configuración para la extracción de texto.

    Returns:
        Diccionario con la configuración
    """
    # Obtener configuración base del text splitter
    config = get_text_converter_config()
    
    config_sftp = get_sftp_config()

    # Expandir con configuraciones adicionales específicas
    config = {
        # Configuración del converter
        'supported_types': config['supported_types'],
        'local_load_directory': config_sftp['local_load_directory'],
    }
    
    return config


