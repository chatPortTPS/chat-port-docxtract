"""
Módulo Keyword Extractor para Document Extractor
===================================================
Módulo que proporciona funcionalidades para la extracción de
keywords y entidades de texto utilizando modelos de NLP.
Uso básico:
    from keywords import KeywordExtractor
    
    extractor = KeywordExtractor()
    keywords = extractor.extract_keywords(text)

"""

from .keyword_extractor import KeywordExtractor
from .config_keywords import load_config

__all__ = [
    'KeywordExtractor',
    'load_config',
]

__version__ = '1.0.0'
