"""
Módulo de Extracción de Palabras Clave
======================================

Proporciona funcionalidad para extraer frases clave de documentos
usando múltiples algoritmos: TF-IDF, RAKE, YAKE y KeyBERT.
"""

from .extractor import KeywordExtractor

__all__ = ['KeywordExtractor']
