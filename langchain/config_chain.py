
from typing import Dict, Any

from config_utils import get_text_splitter_config

def load_config() -> Dict[str, Any]:
    """
    Carga la configuración de LangChain desde el sistema centralizado.
    Alias para compatibilidad con código existente.

    Returns:
        Diccionario con la configuración de LangChain
    """
    # Obtener configuración base del text splitter
    splitter_config = get_text_splitter_config()
    
    # Expandir con configuraciones adicionales específicas de LangChain
    config = {
        # Configuración del splitter
        'chunk_size': splitter_config['chunk_size'],
        'chunk_overlap': splitter_config['chunk_overlap'],
        'separators': ["\n\n", "\n", " ", ""],
        
        # Configuración de metadatos
        'include_fragment_info': True,
        'include_position': True,
        'include_stats': True
    }
    
    return config


def get_splitter_config(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Extrae la configuración específica del text splitter.
    
    Args:
        config: Configuración completa (si no se proporciona, se carga desde dotenv)
        
    Returns:
        Diccionario con configuración del splitter
    """
    if config is None:
        config = load_config()

    return {
        'chunk_size': config.get('chunk_size', 1000),
        'chunk_overlap': config.get('chunk_overlap', 200),
        'separators': config.get('separators', ["\n\n", "\n", " ", ""])
    }


