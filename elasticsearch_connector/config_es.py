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

    # Construir URL de conexión con credenciales embebidas
    if config.get('username') and config.get('password'):
        url = f"{config['scheme']}://{config['username']}:{config['password']}@{config['host']}:{config['port']}"
    else:
        url = f"{config['scheme']}://{config['host']}:{config['port']}"

    # Parámetros en formato correcto para Elasticsearch
    connection_params = {
        'hosts': [url],
        'timeout': config['timeout'],
        'verify_certs': config.get('verify_certs', False),
        'ssl_show_warn': config.get('ssl_show_warn', False)
    }

    # Si se proporciona un certificado CA
    if config.get('ca_cert_path'):
        connection_params['ca_certs'] = config['ca_cert_path']

    return connection_params