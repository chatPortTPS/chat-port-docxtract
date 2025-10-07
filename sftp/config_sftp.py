from config_utils import get_sftp_config

def load_config():
    """Carga la configuración de SFTP desde el sistema centralizado."""
    config = get_sftp_config()
     
    # Mantener estructura compatible con el conector SFTP existente
    return {
        'connection': {
            'hostname': config['hostname'],
            'port': config['port'],
            'username': config['username'],
            'password': config['password'],
            'timeout': config['timeout'],
            'max_retries': config['max_retries']
        },
        'directories': {
            'remote_input_path': config['remote_input_path'], 
            'local_load_directory': config['local_load_directory']
        }
    }