# Módulo de vectorización
"""
Módulo para vectorizar fragmentos de texto usando modelos de embeddings.
"""

from .text_vectorizer import TextVectorizer
from .config_vectors import load_config

__version__ = "1.0.0"
__author__ = "jgonzalez"

__all__ = [
    'TextVectorizer',
    'load_config'
]
