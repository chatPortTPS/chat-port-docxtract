"""
Módulo LangChain Text Splitter Simple para Document Extractor
============================================================

Módulo simplificado que usa únicamente RecursiveCharacterTextSplitter
para dividir texto en fragmentos.

Uso básico:
    from langchain import TextSplitter
    
    splitter = TextSplitter()
    fragments = splitter.split_text("Texto largo a dividir...")
    
    # Resultado: lista de fragmentos con metadatos
    for fragment in fragments:
        print(f"Fragmento {fragment['fragment_index']}: {fragment['text'][:50]}...")
"""

from .text_splitter import TextSplitter
from .config_chain import load_config, get_splitter_config

__all__ = [
    'TextSplitter',
    'load_config',
    'get_splitter_config'
]

__version__ = '1.0.0'
