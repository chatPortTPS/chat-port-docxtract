"""
Document Extractor - Extractor de Documentos
============================================

Módulo principal para extraer contenido de documentos PDF, Word y Excel.
Incluye funcionalidades de limpieza y filtrado de contenido irrelevante.

Autor: Assistant
Fecha: Septiembre 2025
"""

import logging
import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import warnings
import pandas as pd

from .config_text import load_config

from .pdf import Pdf    

# Configurar logging
logger = logging.getLogger(__name__)

class DocumentTextConverter:
    """
    Extractor principal de documentos PDF, Word y Excel.
    
    Maneja la extracción de texto, tablas y metadatos con filtrado
    inteligente de contenido irrelevante.
    """
    
    def __init__(self):
        """Inicializa el extractor con configuración por defecto."""

        config = load_config()
        self.ruta_local = config.get('local_load_directory', './documentos_download')
        self.tipos_soportados = config.get('supported_types', ['.pdf', '.docx', '.xlsx'])

        # Patrones para detectar contenido a filtrar
        self.patrones_indice = [
            r'\b\d+\s*$',  # Números de página al final de línea
            r'\.{3,}\s*\d+\s*$',  # Puntos seguidos de números de página
            r'página\s+\d+',  # Palabra página seguida de número
            r'cap[íi]tulo\s+\d+.*\d+$',  # Capítulo seguido de número de página
        ]
        
        self.palabras_portada = [
            'índice', 'index', 'contenido', 'contents', 'tabla de contenido',
            'table of contents', 'resumen ejecutivo', 'executive summary'
        ]

        self.initialize_supported_types()


    def initialize_supported_types(self):
        """Inicializa los tipos de archivo soportados."""
        self.tipos_soportados = ['.pdf', '.docx', '.xlsx']

        if '.pdf' in self.tipos_soportados:
            print("Soporte para PDF habilitado.")
            self.pdf_extractor = Pdf()


    def extraer_documento(self, nombre_archivo: str) -> Dict[str, Any]:
        """
        Extrae contenido de un documento según su tipo.
        
        Args:
            nombre_archivo: Ruta al archivo a procesar
            
        Returns:
            Diccionario con el contenido extraído estructurado
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el tipo de archivo no es soportado
        """

        print(f"Extrayendo documento: {self.ruta_local}/{nombre_archivo}")
        
        ruta = Path(self.ruta_local) / nombre_archivo

        print(f"Ruta completa del archivo: {ruta}")
        
        if not ruta.exists():
            raise FileNotFoundError(f"El archivo no existe: {self.ruta_local}")
        
        extension = ruta.suffix.lower()
        
        if extension not in self.tipos_soportados:
            raise ValueError(f"Tipo de archivo no soportado: {extension}")
         
        if extension == '.pdf':
            return self.pdf_extractor.procesar_pdf(str(ruta))