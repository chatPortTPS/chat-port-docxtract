import sys
from pathlib import Path

# Añadir el directorio padre al path para importar config_utils centralizado
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_utils import get_vectorization_config

def load_config():
    """Alias para compatibilidad."""

    config = get_vectorization_config()

    return {
        'model_name': config['model_name'],
        'device': config['device'],
        'batch_size': config['batch_size']
    }
 