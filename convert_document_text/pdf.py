import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import warnings
import fitz 
import camelot
import pandas as pd
import unicodedata

class Pdf:
    """
    Clase para extraer y limpiar texto de documentos PDF
    """
    
    def __init__(self):
        print("Inicializando extractor PDF")

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


    def _normalize_text(self, text):
        text = text.lower()
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        return text


    def _es_posible_portada(self, linea: str) -> bool:
        """Determina si una línea podría ser parte de una portada."""
        linea_lower = linea.lower()
        return any(palabra in linea_lower for palabra in self.palabras_portada)

    def _reconstruir_parrafos(self, lineas: List[str]) -> str:
        """Reconstruye párrafos a partir de líneas fragmentadas."""
        parrafos = []
        parrafo_actual = []
        
        for linea in lineas:
            # Si la línea termina con punto, es fin de párrafo
            if linea.endswith('.') or linea.endswith('!') or linea.endswith('?'):
                parrafo_actual.append(linea)
                parrafos.append(' '.join(parrafo_actual))
                parrafo_actual = []
            # Si la línea parece ser continuación
            elif parrafo_actual and linea[0].islower():
                parrafo_actual.append(linea)
            # Nueva oración/párrafo
            else:
                if parrafo_actual:
                    parrafos.append(' '.join(parrafo_actual))
                parrafo_actual = [linea]
        
        # Agregar el último párrafo si existe
        if parrafo_actual:
            parrafos.append(' '.join(parrafo_actual))
        
        return '\n\n'.join(parrafos)

    def _extraer_metadatos_pdf(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extrae metadatos de un documento PDF."""
        metadatos = doc.metadata
        return {
            'titulo': metadatos.get('title', ''),
            'autor': metadatos.get('author', ''),
            'fecha_creacion': metadatos.get('creationDate', ''),
            'fecha_modificacion': metadatos.get('modDate', ''),
            'paginas': len(doc)
        }
    


    def _procesar_tablas_camelot(self, tablas) -> List[Dict[str, Any]]:
        """Procesa tablas extraídas con Camelot."""
        tablas_procesadas = []
        
        for i, tabla in enumerate(tablas):
            try:
                df = tabla.df
                
                # Convertir a lista de diccionarios
                if not df.empty:
                    # Usar la primera fila como encabezados si no están vacíos
                    if df.iloc[0].notna().all():
                        df.columns = df.iloc[0]
                        df = df.drop(df.index[0])
                    
                    # Filtrar filas completamente vacías
                    df = df.dropna(how='all')
                    
                    if not df.empty:
                        datos = df.to_dict('records')
                        tablas_procesadas.append({
                            'indice': i + 1,
                            'datos': datos,
                            'filas': len(datos),
                            'columnas': len(df.columns)
                        })
            
            except Exception as e:
                print(f"Error procesando tabla {i + 1}: {e}")
                continue

        return tablas_procesadas
    
    def _encontrar_texto_repetitivo(self, lineas: List[str]) -> List[str]:
        """Encuentra texto que se repite en múltiples páginas."""
        if len(lineas) < 2:
            return []
        
        contador = {}
        for linea in lineas:
            linea = linea.strip()
            if linea and len(linea) > 5:  # Ignorar líneas muy cortas
                contador[linea] = contador.get(linea, 0) + 1
        
        # Considerar repetitivo si aparece en más del 50% de las páginas
        umbral = len(lineas) * 0.5
        repetitivos = [linea for linea, count in contador.items() if count > umbral]
        return repetitivos
    
    
    def _es_linea_indice(self, linea: str) -> bool:
        """Determina si una línea parece ser parte de un índice."""
        for patron in self.patrones_indice:
            if re.search(patron, linea, re.IGNORECASE):
                return True
        return False

    def _limpiar_texto_pdf(self, texto_paginas: List[str], 
                          cabeceras_repetitivas: List[str], 
                          pies_repetitivos: List[str]) -> str:
        """Limpia el texto del PDF removiendo contenido irrelevante."""
        texto_limpio = []
        
        for i, texto_pagina in enumerate(texto_paginas):
            lineas = texto_pagina.strip().split('\n')
            lineas_filtradas = []
            
            for linea in lineas:
                linea = linea.strip()
                
                # Saltar líneas vacías
                if not linea:
                    continue
                
                # Filtrar cabeceras y pies repetitivos
                if linea in cabeceras_repetitivas or linea in pies_repetitivos:
                    continue
                
                # Filtrar líneas que parecen índice
                if self._es_linea_indice(linea):
                    continue
                
                # Si es la primera página y parece portada, saltar
                if i == 0 and self._es_posible_portada(linea):
                    continue
                
                lineas_filtradas.append(linea)
            
            # Reconstruir párrafos
            if lineas_filtradas:
                texto_reconstruido = self._reconstruir_parrafos(lineas_filtradas)
                texto_limpio.append(texto_reconstruido)
        
        texto_final = ' '.join(texto_limpio)
        texto_final = texto_final.replace('\n\n', ' ')

        return self._normalize_text(texto_final)


    def procesar_pdf(self, ruta_archivo: str) -> Dict[str, Any]:
        """
        Procesa un archivo PDF extrayendo texto, tablas y metadatos.
        
        Args:
            ruta_archivo: Ruta al archivo PDF
            
        Returns:
            Diccionario con contenido estructurado del PDF
        """
        resultado = {
            'tipo_archivo': 'pdf',
            'archivo': Path(ruta_archivo).name,
            'metadatos': {},
            'contenido': {
                'texto': '',
                'tablas': []
            }
        }
        
        # Abrir el documento PDF
        doc = fitz.open(ruta_archivo)
        
        try:
            # Extraer metadatos
            resultado['metadatos'] = self._extraer_metadatos_pdf(doc)
            
            # Extraer texto de todas las páginas
            texto_paginas = []
            cabeceras_comunes = []
            pies_comunes = []
            
            for num_pagina in range(len(doc)):
                pagina = doc[num_pagina]
                texto_pagina = pagina.get_text()
                
                if texto_pagina.strip():
                    texto_paginas.append(texto_pagina)
                    
                    # Detectar posibles cabeceras y pies
                    lineas = texto_pagina.strip().split('\n')
                    if lineas:
                        cabeceras_comunes.append(lineas[0])
                        if len(lineas) > 1:
                            pies_comunes.append(lineas[-1])
            
            # Identificar cabeceras y pies repetitivos
            cabeceras_repetitivas = self._encontrar_texto_repetitivo(cabeceras_comunes)
            pies_repetitivos = self._encontrar_texto_repetitivo(pies_comunes)
            
            # Limpiar y procesar el texto
            texto_completo = self._limpiar_texto_pdf(
                texto_paginas, cabeceras_repetitivas, pies_repetitivos
            )
            
            resultado['contenido']['texto'] = texto_completo
            
            # Extraer tablas usando Camelot
            try:
                tablas = camelot.read_pdf(ruta_archivo, pages='all', flavor='lattice')
                resultado['contenido']['tablas'].extend(
                    self._procesar_tablas_camelot(tablas)
                )
            except Exception as e:
                print(f"Advertencia: No se pudieron extraer tablas con Camelot: {e}")
                # Intentar con flavor 'stream' como alternativa
                try:
                    tablas = camelot.read_pdf(ruta_archivo, pages='all', flavor='stream')
                    resultado['contenido']['tablas'].extend(
                        self._procesar_tablas_camelot(tablas)
                    )
                except Exception as e2:
                    print(f"Advertencia: Falló también la extracción alternativa de tablas: {e2}")
        
        finally:
            doc.close()
        
        return resultado