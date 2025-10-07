"""
Módulo LangChain Text Splitter Simple para Document Extractor
============================================================

Módulo simplificado que usa únicamente RecursiveCharacterTextSplitter
para dividir texto en fragmentos.

Uso básico:
 
"""

from .config_text import load_config

__all__ = [
    'DocumentTextConverter',
    'load_config'
]

__version__ = '1.0.0'
