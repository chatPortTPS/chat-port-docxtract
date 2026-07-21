"""
Modelo Compartido - Singleton
==============================

Módulo para cargar y compartir el modelo de SentenceTransformer
entre diferentes componentes (TextVectorizer y KeywordExtractor).

Esto evita la carga duplicada del modelo, mejorando el rendimiento
y reduciendo el uso de memoria.
"""

import logging
from typing import Optional, TYPE_CHECKING

# Import condicional para type hints
if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers no instalado")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("torch no instalado. Se usará CPU")


class SharedModelManager:
    """
    Gestor Singleton del modelo compartido de SentenceTransformer.
    
    Asegura que el modelo se cargue solo una vez y se comparta
    entre todos los componentes que lo necesiten.
    """
    
    _instance: Optional['SharedModelManager'] = None
    _model: Optional['SentenceTransformer'] = None  # String literal para evitar error de tipo
    _model_name: Optional[str] = None
    _device: Optional[str] = None
    
    def __new__(cls):
        """Implementación del patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_model(cls, model_name: str = "Qwen/Qwen3-Embedding-0.6B", 
                  device: str = "auto"):
        """
        Obtiene la instancia del modelo compartido.
        
        Si el modelo no ha sido cargado, lo carga. Si ya existe pero se solicita
        un modelo diferente, recarga el nuevo modelo.
        
        Args:
            model_name: Nombre del modelo de sentence-transformers
            device: Dispositivo a usar ('cpu', 'cuda', 'auto')
            
        Returns:
            Instancia del modelo SentenceTransformer
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers no está disponible. "
                "Instale con: pip install sentence-transformers"
            )
        
        # Determinar dispositivo
        resolved_device = cls._determine_device(device)
        
        # Verificar si necesitamos cargar/recargar el modelo
        if (cls._model is None or 
            cls._model_name != model_name or 
            cls._device != resolved_device):
            
            logger.info(f"Cargando modelo compartido: {model_name} en {resolved_device}...")
            
            try:
                cls._model = SentenceTransformer(model_name, device=resolved_device)
                cls._model_name = model_name
                cls._device = resolved_device
                
                dimension = cls._model.get_sentence_embedding_dimension()
                logger.info(
                    f"Modelo compartido cargado exitosamente. "
                    f"Dimensiones: {dimension}, Dispositivo: {resolved_device}"
                )
                
            except Exception as e:
                logger.error(f"Error cargando modelo compartido: {e}")
                raise RuntimeError(f"Error cargando modelo {model_name}: {e}")
        else:
            logger.debug(f"Reutilizando modelo compartido ya cargado: {model_name}")
        
        return cls._model
    
    @classmethod
    def _determine_device(cls, device: str) -> str:
        """Determina el dispositivo a usar para los cálculos."""
        if device == "auto":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return device
    
    @classmethod
    def is_loaded(cls) -> bool:
        """Verifica si el modelo ya ha sido cargado."""
        return cls._model is not None
    
    @classmethod
    def get_model_info(cls) -> dict:
        """
        Obtiene información sobre el modelo cargado.
        
        Returns:
            Diccionario con información del modelo o None si no está cargado
        """
        if cls._model is None:
            return {
                'loaded': False,
                'model_name': None,
                'device': None,
                'dimension': None
            }
        
        return {
            'loaded': True,
            'model_name': cls._model_name,
            'device': cls._device,
            'dimension': cls._model.get_sentence_embedding_dimension()
        }
    
    @classmethod
    def clear(cls):
        """Limpia el modelo de la memoria (útil para testing o reinicios)."""
        if cls._model is not None:
            logger.info("Liberando modelo compartido de la memoria...")
            del cls._model
            cls._model = None
            cls._model_name = None
            cls._device = None


# Función de conveniencia para obtener el modelo
def get_shared_model(model_name: str = "Qwen/Qwen3-Embedding-0.6B", 
                     device: str = "auto"):
    """
    Función de conveniencia para obtener el modelo compartido.
    
    Args:
        model_name: Nombre del modelo de sentence-transformers
        device: Dispositivo a usar ('cpu', 'cuda', 'auto')
        
    Returns:
        Instancia del modelo SentenceTransformer
    """
    return SharedModelManager.get_model(model_name, device)
