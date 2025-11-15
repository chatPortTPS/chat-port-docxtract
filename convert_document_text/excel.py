from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import unicodedata


class Excel:
    """
    Clase para extraer datos de archivos Excel (.xlsx)
    """

    def __init__(self):
        print("Inicializando extractor Excel")

    def _normalize_text(self, text):
        """Normaliza el texto eliminando acentos y convirtiendo a minúsculas."""
        if not isinstance(text, str):
            text = str(text)
        text = text.lower()
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        return text

    def _procesar_hoja(self, df: pd.DataFrame, nombre_hoja: str, indice: int) -> Dict[str, Any]:
        """Procesa una hoja de Excel."""
        try:
            # Limpiar DataFrame
            df = df.dropna(how='all')  # Eliminar filas completamente vacías
            df = df.dropna(axis=1, how='all')  # Eliminar columnas completamente vacías

            if df.empty:
                return None

            # Extraer texto de todas las celdas
            texto_celdas = []
            for col in df.columns:
                valores = df[col].dropna().astype(str).tolist()
                texto_celdas.extend(valores)

            # Convertir a lista de diccionarios
            datos = df.to_dict('records')

            return {
                'indice': indice,
                'nombre_hoja': nombre_hoja,
                'datos': datos,
                'texto': ' '.join(texto_celdas),
                'filas': len(df),
                'columnas': len(df.columns)
            }
        except Exception as e:
            print(f"Error procesando hoja '{nombre_hoja}': {e}")
            return None

    def procesar_excel(self, ruta_archivo: str) -> Dict[str, Any]:
        """
        Procesa un archivo Excel extrayendo datos de todas las hojas.

        Args:
            ruta_archivo: Ruta al archivo Excel

        Returns:
            Diccionario con contenido estructurado del archivo Excel
        """
        resultado = {
            'tipo_archivo': 'excel',
            'archivo': Path(ruta_archivo).name,
            'metadatos': {},
            'contenido': {
                'texto': '',
                'hojas': []
            }
        }

        try:
            # Leer todas las hojas del archivo Excel
            excel_file = pd.ExcelFile(ruta_archivo)
            nombres_hojas = excel_file.sheet_names

            resultado['metadatos'] = {
                'numero_hojas': len(nombres_hojas),
                'nombres_hojas': nombres_hojas
            }

            # Procesar cada hoja
            texto_completo = []
            hojas_procesadas = []

            for i, nombre_hoja in enumerate(nombres_hojas):
                df = pd.read_excel(ruta_archivo, sheet_name=nombre_hoja)
                hoja_procesada = self._procesar_hoja(df, nombre_hoja, i + 1)

                if hoja_procesada:
                    hojas_procesadas.append(hoja_procesada)
                    texto_completo.append(hoja_procesada['texto'])

            resultado['contenido']['hojas'] = hojas_procesadas
            resultado['contenido']['texto'] = self._normalize_text(' '.join(texto_completo))

        except Exception as e:
            print(f"Error procesando archivo Excel: {e}")
            raise

        return resultado
