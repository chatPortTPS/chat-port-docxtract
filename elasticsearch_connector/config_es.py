from config_utils import get_elasticsearch_config
 
def load_config():
    """Alias para compatibilidad."""
    return get_elasticsearch_config()


def get_connection_params():
    """
    Genera los parámetros de conexión compatibles con la librería Elasticsearch.
    """
    config = load_config()

    if not config:
        raise RuntimeError("Configuración de Elasticsearch no encontrada.")
    
    # Construir URL de conexión
    url = f"{config['scheme']}://{config['host']}:{config['port']}"
    
    # Parámetros en formato correcto para Elasticsearch
    connection_params = {
        'hosts': [url],
        'timeout': config['timeout']
    }
    
    # Añadir autenticación si está configurada
    if config.get('username') and config.get('password'):
        connection_params['basic_auth'] = (config['username'], config['password'])
    
    return connection_params