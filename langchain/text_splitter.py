"""
LangChain Text Splitter - Document Extractor
============================================

Módulo para dividir texto en fragmentos usando LangChain text splitters.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from pathlib import Path

# Configurar logging
logger = logging.getLogger(__name__)

# Dependencias de LangChain
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False

from .config_chain import load_config, get_splitter_config


class TextSplitter:
    """
    Clase para dividir texto en fragmentos usando diferentes estrategias de LangChain.
    """
    
    def __init__(self):
        """
        Inicializa el text splitter
         
        """
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain no está disponible. Instale con: pip install langchain") 
            return

        self.config = load_config()

        if not self.config:
            logger.error("No se pudo cargar la configuración de LangChain, Verifique el archivo las variables de entorno")
            return
        
        self.splitter_config = get_splitter_config(self.config)
        self.metadata_config = self.config.get('metadata', {})
        
        # Inicializar el splitter
        self.splitter = self._create_splitter()
    

    def _create_splitter(self):
        """
        Crea el text splitter RecursiveCharacterTextSplitter
        
        Returns:
            Instancia del text splitter configurado
        """
        return RecursiveCharacterTextSplitter(
            chunk_size=self.splitter_config['chunk_size'],
            chunk_overlap=self.splitter_config['chunk_overlap'],
            separators=self.splitter_config['separators']
        )
    
    def split_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Divide el texto en fragmentos
        
        Args:
            text: Texto a dividir 
        Returns:
            Lista de fragmentos con metadatos
        """
        if not text or not text.strip():
            logger.warning("No se proporcionó texto para dividir")
            raise RuntimeError("No se proporcionó texto para dividir.")
        
        # Si LangChain no está disponible, usar método simple
        if not LANGCHAIN_AVAILABLE or self.splitter is None:
            raise RuntimeError("LangChain no está disponible, debe instalarse.")
        
        try:
            logger.info(f"Dividiendo texto de {len(text)} caracteres usando RecursiveCharacterTextSplitter")
            
            # Dividir texto usando LangChain
            chunks = self.splitter.split_text(text)
            
            logger.info(f"Texto dividido en {len(chunks)} fragmentos")
            
            # Crear fragmentos con metadatos
            fragments = []
            for i, chunk in enumerate(chunks):
                fragment = self._create_fragment(chunk, i, len(chunks), text)
                fragments.append(fragment)
            
            return fragments
            
        except Exception as e:
            logger.error(f"Error dividiendo texto con LangChain: {e}") 
            raise RuntimeError(f"Algún error ocurrió al dividir el texto con LangChain, mensaje de error: {e}")


    def _create_fragment(self, chunk: str, index: int, total_chunks: int,
                        original_text: str) -> Dict[str, Any]:
        """
        Crea un fragmento con metadatos
        
        Args:
            chunk: Texto del fragmento
            index: Índice del fragmento
            total_chunks: Total de fragmentos
            original_text: Texto original completo
            
        Returns:
            Diccionario con el fragmento y sus metadatos
        """
        fragment = {
            'text': chunk.strip(),
            'fragment_id': f"fragment_{index:03d}"
        }
        
        # Agregar información básica del fragmento si está configurado
        if self.metadata_config.get('include_fragment_info', True):
            fragment.update({
                'fragment_index': index,
                'total_fragments': total_chunks,
                'splitter_type': 'recursive_character'
            })
        
        # Agregar posición original si está configurado
        if self.metadata_config.get('include_position', True):
            start_pos = original_text.find(chunk.strip())
            if start_pos != -1:
                end_pos = start_pos + len(chunk.strip())
                fragment.update({
                    'start_position': start_pos,
                    'end_position': end_pos,
                    'position_percentage': round((start_pos / len(original_text)) * 100, 2)
                })
        
        # Agregar estadísticas si está configurado
        if self.metadata_config.get('include_stats', True):
            fragment.update({
                'character_count': len(chunk.strip()),
                'word_count': len(chunk.strip().split()),
                'line_count': len(chunk.strip().split('\n'))
            })
        
        # Agregar timestamp de procesamiento
        fragment['processed_at'] = datetime.now().isoformat()
        
        return fragment    
