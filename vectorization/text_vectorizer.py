"""
Módulo de Vectorización - Document Extractor
============================================

Módulo para vectorizar fragmentos de texto usando modelos de embeddings.
Utiliza sentence-transformers para generar embeddings de alta calidad.

"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
import time

# Configurar logging
logger = logging.getLogger(__name__)

# Dependencias de vectorización
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers no instalado. Ejecute: pip install sentence-transformers")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("torch no instalado. Se usará CPU para vectorización")

# Importar el gestor de modelo compartido
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_model import get_shared_model

from .config_vectors import load_config

class TextVectorizer:
    """
    Clase para vectorizar texto usando modelos pre-entrenados.
    
    Soporta diferentes modelos de sentence-transformers optimizados
    para diferentes idiomas y casos de uso.
    """
    
    def __init__(self, device: str = "auto"):
        """
        Inicializa el vectorizador.
        
        Args:
            device: Dispositivo a usar ('cpu', 'cuda', 'auto')
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers no está disponible. Instale con: pip install sentence-transformers")
        
        config = load_config()

        self.model_name = config['model_name']
        self.batch_size = config.get('batch_size', 32)
        self.device = device
        
        logger.info(f"Inicializando vectorizador con modelo compartido: {self.model_name}")
        
        # Obtener el modelo compartido (se carga solo la primera vez)
        self.model = get_shared_model(model_name=self.model_name, device=device)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"Vectorizador inicializado. Dimensiones: {self.embedding_dimension}")
    

    def vectorize_text(self, text: str, normalize: bool = True) -> List[float]:
        """
        Vectoriza un texto individual.
        
        Args:
            text: Texto a vectorizar
            normalize: Si normalizar el vector resultante
            
        Returns:
            Vector de embeddings como lista de floats
        """
        if not self.model:
            raise RuntimeError("Modelo no inicializado")
        
        try:
             
            # Generar embedding
            embedding = self.model.encode(text, normalize_embeddings=normalize)
            
            # Convertir a lista de floats
            if isinstance(embedding, np.ndarray):
                embedding_list = embedding.tolist()
            else:
                embedding_list = list(embedding)
             
            return embedding_list
            
        except Exception as e:
            raise RuntimeError(f"Error vectorizando texto: {e}")
    

    def vectorize_texts(self, texts: List[str], batch_size: int = 32, normalize: bool = True) -> List[List[float]]:
        """
        Vectoriza múltiples textos en lotes para mejor rendimiento.
        
        Args:
            texts: Lista de textos a vectorizar
            batch_size: Tamaño del lote para procesamiento
            normalize: Si normalizar los vectores resultantes / busqueda por similitud coseno
            
        Returns:
            Lista de vectores de embeddings
        """
        if not self.model:
            raise RuntimeError("Modelo no inicializado")
        
        if not texts:
            raise RuntimeError("No se proporcionaron textos para vectorizar")
        
        try:
            logger.info(f"Vectorizando {len(texts)} textos en lotes de {batch_size}...")
            
            # Procesar en lotes
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch_texts, 
                    normalize_embeddings=normalize,
                    batch_size=batch_size,
                    show_progress_bar=False
                )
                
                # Convertir a listas
                if isinstance(batch_embeddings, np.ndarray):
                    batch_embeddings_list = batch_embeddings.tolist()
                else:
                    batch_embeddings_list = [list(emb) for emb in batch_embeddings]
                
                all_embeddings.extend(batch_embeddings_list)
                
                logger.debug(f"Procesado lote {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
              
            logger.info(f"Vectorización completada. {len(all_embeddings)} embeddings generados.")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error vectorizando textos: {e}")
            raise RuntimeError(f"Error vectorizando textos: {e}")
    

    def vectorize_fragments(self, fragments: List[Dict[str, Any]], text_key: str = 'text') -> List[Dict[str, Any]]:
        """
        Vectoriza fragmentos de texto agregando embeddings a cada fragmento.
        
        Args:
            fragments: Lista de fragmentos con estructura de diccionario
            text_key: Clave que contiene el texto en cada fragmento
            
        Returns:
            Lista de fragmentos con embeddings agregados
        """
        if not fragments:
            raise RuntimeError("No se proporcionaron fragmentos para vectorizar")
        
        try:
            logger.info(f"Vectorizando {len(fragments)} fragmentos...")
            
            # Extraer textos
            texts = []
            valid_indices = []
            
            for i, fragment in enumerate(fragments):
                text = fragment.get(text_key, '')
                if text and text.strip():
                    texts.append(text.strip())
                    valid_indices.append(i)
                else:
                    logger.warning(f"Fragmento {i} sin texto válido")
            
            if not texts:
                logger.warning("No hay textos válidos para vectorizar")
                raise RuntimeError("No hay textos válidos para vectorizar")
            
            # Vectorizar textos
            embeddings = self.vectorize_texts(texts)
            
            if len(embeddings) != len(texts):
                logger.error("Número de embeddings no coincide con número de textos")
                raise RuntimeError("Número de embeddings no coincide con número de textos")

            # Agregar embeddings a fragmentos
            result_fragments = []
            embedding_index = 0
            
            for i, fragment in enumerate(fragments):
                result_fragment = fragment.copy()
                
                if i in valid_indices:
                    result_fragment['embedding_vector'] = embeddings[embedding_index]
                    result_fragment['embedding_dimension'] = len(embeddings[embedding_index])
                    result_fragment['embedding_model'] = self.model_name
                    embedding_index += 1
                else:
                    # Fragmento sin texto válido - usar vector vacío
                    result_fragment['embedding_vector'] = []
                    result_fragment['embedding_dimension'] = 0
                    result_fragment['embedding_model'] = None
                
                result_fragments.append(result_fragment)
            
            logger.info(f"Vectorización de fragmentos completada. {len(texts)} embeddings generados.")
            
            return result_fragments
            
        except Exception as e:
            logger.error(f"Error vectorizando fragmentos: {e}")
            raise RuntimeError("Error vectorizando fragmentos")
    
    

    

