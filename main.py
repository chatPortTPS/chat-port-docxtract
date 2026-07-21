"""
Servicio de Procesamiento de Documentos
=======================================

Servicio principal que integra todos los componentes disponibles:
- SFTP (descarga de archivos)
- Document Extractor (extracción de contenido)
- LangChain (fragmentación de texto) - opcional
- Elasticsearch (indexación con vectores) - opcional
- Artemis (recepción de mensajes) - opcional

"""

import json
import logging
import os
from platform import processor
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import time
import traceback

# Configurar logging solo para terminal o el stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

from sftp.connector import SftpConnector
from convert_document_text.converter import DocumentTextConverter
from langchain.text_splitter import TextSplitter
from vectorization.text_vectorizer import TextVectorizer
from keywords import KeywordExtractor
from elasticsearch_connector.connector import ElasticsearchConnector
from artemis import ArtemisConnector
from shared_model import get_shared_model
from config_utils import get_vectorization_config


class DocumentProcessor:
    """Aplicación principal del sistema de procesamiento de documentos."""

    def __init__(self, text_vectorizer: TextVectorizer):
        """Inicializa el procesador de documentos."""
        self.sftp_connector = None
        self.document_text_converter = None
        self.document_uuid = None
        self.texto = None
        self.splitter = None
        self.fragments = []
        self.vectorizer = text_vectorizer 
        self.keywords = []
        self.keywords_globales = []
        self.areas = None

        self.nombre = None
        self.privacidad = None
        self.creacion = None
        self.actualizacion = None
        self.correo = None
        self.autor = None
        self.ruta = None
        self.agente = None 
        self.keyword_extractor = None

        self._initialize_components()


    def _initialize_components(self):
        """Inicializa los componentes disponibles."""
        self.sftp_connector = SftpConnector()
        self.document_text_converter = DocumentTextConverter()
        self.splitter = TextSplitter()
        self.es_connector = ElasticsearchConnector()
        self.keyword_extractor = KeywordExtractor()
 
    def download_file(self):
        if self.sftp_connector is None:
            print("Error: SFTP Connector no está disponible")
            return False
        
        try:
            self.sftp_connector.connect()
            self.sftp_connector.download_file(self.document_uuid)
            self.sftp_connector.disconnect()
            return True
        except Exception as e:
            print(f"Error descargando archivo: {e}")
            return False

    def extraer_documento(self):
        """Extrae el contenido del documento descargado."""
        self.texto = self.document_text_converter.extraer_documento(nombre_archivo=self.document_uuid)
        return self.texto

    def extract_keywords_global(self) -> List[str]:
        """Extrae palabras clave globales del documento usando el algoritmo configurado."""
        if self.keyword_extractor is None:
            raise ValueError("KeywordExtractor no está disponible")
 
        if not self.texto:
            raise ValueError("No hay texto para extraer keywords globales")
        
        texto_completo = self.texto.get('contenido', {}).get('texto', '')
        self.keywords_globales = self.keyword_extractor.get_keywords_keybert_documento(texto_completo, k=10)
        
        return self.keywords_globales

    def extract_keywords_fragments(self) -> List[Dict[str, Any]]:
        """Extrae palabras clave del documento usando el algoritmo configurado."""
        if self.keyword_extractor is None:
            raise ValueError("KeywordExtractor no está disponible")
 
        if not self.fragments:
            raise ValueError("No hay fragmentos para extraer palabras clave")
 
        for fragment in self.fragments:
            texto_fragmento = fragment.get('content_raw', '')
            keywords_fragmento = self.keyword_extractor.get_keywords_keybert_documento(texto_fragmento, k=5)
            fragment['metadata']['keywords'] = keywords_fragmento
            fragment['metadata']['keywords_globales'] = self.keywords_globales

        self.keywords = [fragment['metadata']['keywords'] for fragment in self.fragments]
        
        return self.keywords

    def split_text(self) -> List[Dict[str, Any]]:
        """Divide el texto en fragmentos usando LangChain."""
        if self.splitter is None:
            raise ValueError("TextSplitter no está disponible")
        
        texto_completo = self.texto.get('contenido', {}).get('texto', '')

        if not texto_completo:
            raise ValueError("No hay texto para dividir")

        fragments = self.splitter.split_text(texto_completo)
        self.fragments = [self._formato_fragmento(fragment) for fragment in fragments]
        return self.fragments

    def _formato_fragmento(self, fragment: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea un fragmento en la estructura requerida."""
        return {
            "doc_id": self.document_uuid,
            "chunk_index": fragment.get('fragment_index', 0),
            "page": self.texto.get('metadatos', {}).get('paginas', 0),
            "section": "",
            "tokens": 0,

            "areas": self.areas,
            "metadata": {
                "titulo": self.nombre,
                "autor": self.autor,
                "fecha_creacion": self.creacion,
                "fecha_modificacion": self.actualizacion,
                "correo": self.correo,
                "privacidad": self.privacidad,
                "agente": self.agente,
                "keywords": self.keywords,
                "keywords_globales": self.keywords_globales
            },

            "ruta": self.ruta,

            "content_raw": fragment.get('text', ''),
            "title": self.nombre,
            "source_url": self.document_uuid,

            "content_vector": []
        }

    def vectorize_fragments(self) -> List[Dict[str, Any]]:
        """Vectoriza los fragmentos de texto."""
        if self.vectorizer is None:
            raise ValueError("TextVectorizer no está disponible")

        for fragment in self.fragments:
            text = fragment.get('content_raw', '')
            vector = self.vectorizer.vectorize_text(text)
            fragment['content_vector'] = vector
 
        return self.fragments
     
    def send_to_elasticsearch(self, fragment: Dict[str, Any]) -> bool:
        """Envía un fragmento a Elasticsearch.""" 
        try:
            self.es_connector.connect() 
            success = self.es_connector.save_document(fragment, self.document_uuid) 
            self.es_connector.disconnect()
            return success
        except Exception as e:
            print(f"Error enviando fragmento a Elasticsearch: {e}")
            return False
    
    def delete_document_from_elasticsearch(self) -> bool:
        """Elimina un documento de Elasticsearch usando su doc_id."""
        try:
            self.es_connector.connect() 
            success = self.es_connector.delete_document(self.document_uuid) 
            self.es_connector.disconnect()
            return success
        except Exception as e:
            print(f"Error eliminando documento de Elasticsearch: {e}")
            return False


def bulk_load_documents():
    """
    Carga masiva de documentos desde el archivo init.jsonl en la raíz del proyecto.
    Procesa cada línea del archivo JSONL y espera 1 minuto entre cada documento.
    """
    try:
        # Pre-cargar el modelo compartido ANTES de crear instancias
        logger.info("=== PRE-CARGANDO MODELO COMPARTIDO ===")
        vector_config = get_vectorization_config()
        model = get_shared_model(
            model_name=vector_config['model_name'],
            device=vector_config.get('device', 'auto')
        )
        logger.info(f"Modelo compartido pre-cargado: {vector_config['model_name']}")
        logger.info("="*50)
        
        # Inicializar TextVectorizer (ahora reutilizará el modelo ya cargado)
        logger.info("Inicializando TextVectorizer...")
        text_vectorizer = TextVectorizer()
        logger.info("TextVectorizer inicializado correctamente")

        # Ruta al archivo init.jsonl en la raíz
        init_file_path = Path(__file__).parent / "init.jsonl"
        
        if not init_file_path.exists():
            logger.error(f"No se encontró el archivo {init_file_path}")
            print(f"Error: No se encontró el archivo init.jsonl en la ruta: {init_file_path}")
            return

        # Leer el archivo JSONL línea por línea
        with open(init_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            total_documents = len(lines)
            logger.info(f"Se encontraron {total_documents} documentos para procesar")
            print(f"\n{'='*60}")
            print(f"Iniciando carga masiva de {total_documents} documentos")
            print(f"{'='*60}\n")

            for index, line in enumerate(lines, start=1):
                try:
                    # Parsear la línea JSON
                    message = json.loads(line.strip())
                    
                    datos_array = message.get('datos', [])
                    data = datos_array[0] if datos_array else {}
                    
                    if not data:
                        logger.warning(f"Documento {index}/{total_documents}: No contiene datos válidos, omitiendo...")
                        continue

                    # Crear un nuevo procesador para cada documento
                    processor = DocumentProcessor(text_vectorizer)
                    processor.document_uuid = data.get('archivo')
                    processor.areas = data.get('areas', [])
                    processor.nombre = data.get('nombre')
                    processor.privacidad = data.get('privacidad')
                    processor.creacion = data.get('creacion')
                    processor.actualizacion = data.get('actualizacion')
                    processor.correo = data.get('correo')
                    processor.autor = data.get('autor')
                    processor.ruta = data.get('ruta')
                    processor.agente = data.get('agente', '')

                    if not processor.document_uuid:
                        logger.warning(f"Documento {index}/{total_documents}: No contiene 'archivo', omitiendo...")
                        continue

                    # Procesar areas
                    if processor.areas and isinstance(processor.areas, str):
                        processor.areas = processor.areas.split(',')
                    if not processor.areas or not isinstance(processor.areas, list):
                        processor.areas = []

                    if not processor.agente or not isinstance(processor.agente, str):
                        processor.agente = ""

                    print(f"\n[{index}/{total_documents}] Procesando: {processor.nombre}")
                    print(f"    Archivo: {processor.document_uuid}")
                    logger.info(f"Procesando documento {index}/{total_documents}: {processor.document_uuid}")

                    # 1. Descargar archivo desde SFTP
                    logger.info(f"Descargando archivo desde SFTP...")
                    success = processor.download_file()
                    if not success:
                        logger.error(f"Error descargando archivo {processor.document_uuid}")
                        print(f"     Error descargando archivo")
                        continue

                    # 2. Extraer texto del documento
                    logger.info(f"Extrayendo texto del documento...")
                    processor.extraer_documento()
                    if not processor.texto:
                        logger.error(f"Error extrayendo texto de {processor.document_uuid}")
                        print(f"     Error extrayendo texto")
                        continue

                    # 3. Extraer keywords globales
                    logger.info(f"Extrayendo keywords globales del documento...")
                    processor.extract_keywords_global()
                    if not processor.keywords_globales:
                        logger.error(f"Error extrayendo keywords globales de {processor.document_uuid}")
                        print(f"     Error extrayendo keywords globales")
                        continue

                    # 4. Dividir texto en fragmentos
                    logger.info(f"Dividiendo texto en fragmentos...")
                    fragments = processor.split_text()
                    if not fragments:
                        logger.error(f"Error creando fragmentos de {processor.document_uuid}")
                        print(f"     Error creando fragmentos")
                        continue

                    # Extraer keywords por fragmento
                    logger.info(f"Extrayendo keywords por fragmento...")
                    processor.extract_keywords_fragments()
                    

                    # 5. Vectorizar fragmentos
                    logger.info(f"Vectorizando {len(fragments)} fragmentos...")
                    processor.vectorize_fragments()
                    if not processor.fragments:
                        logger.error(f"Error vectorizando fragmentos de {processor.document_uuid}")
                        print(f"     Error vectorizando fragmentos")
                        continue

                    # 6. Eliminar documento existente (si existe)
                    logger.info(f"Eliminando documento previo (si existe)...")
                    processor.delete_document_from_elasticsearch()

                    # 7. Guardar fragmentos en Elasticsearch
                    logger.info(f"Guardando {len(processor.fragments)} fragmentos en Elasticsearch...")
                    for i, fragment in enumerate(processor.fragments):
                        success = processor.send_to_elasticsearch(fragment)
                        if not success:
                            logger.warning(f"Error guardando fragmento {i+1}/{len(processor.fragments)}")

                    print(f"    ✓ Procesado exitosamente ({len(processor.fragments)} fragmentos)")
                    logger.info(f"Documento {processor.document_uuid} procesado exitosamente")
 
                except json.JSONDecodeError as e:
                    logger.error(f"Error parseando JSON en línea {index}: {e}")
                    print(f"[{index}/{total_documents}]  Error parseando JSON")
                    continue
                except Exception as e:
                    logger.error(f"Error procesando documento {index}: {e}")
                    logger.error(traceback.format_exc())
                    print(f"[{index}/{total_documents}]  Error: {e}")
                    continue

          
            print(f"\n{'='*60}")
            print(f"Carga masiva completada")
            print(f"{'='*60}\n")
            logger.info("Proceso de carga masiva completado")

    except Exception as e:
        logger.error(f"Error en la carga masiva de documentos: {e}")
        logger.error(traceback.format_exc())
        print(f"Error en la carga masiva: {e}")

        
def main():
    
    try:
        # Pre-cargar el modelo compartido ANTES de crear instancias
        logger.info("=== PRE-CARGANDO MODELO COMPARTIDO ===")
        vector_config = get_vectorization_config()
        model = get_shared_model(
            model_name=vector_config['model_name'],
            device=vector_config.get('device', 'auto')
        )
        logger.info(f"Modelo compartido pre-cargado: {vector_config['model_name']}")
        logger.info("="*50)

        # 1. Inicializar TextVectorizer (ahora reutilizará el modelo ya cargado)
        logger.info("Inicializando TextVectorizer...")
        text_vectorizer = TextVectorizer()
        logger.info("TextVectorizer inicializado correctamente")

        # 2. Inicializar ArtemisConnector posterior a la carga del modelo
        artemis_connector = ArtemisConnector()

  
        def handler(message: Dict[str, Any]):
            """Maneja un mensaje recibido de Artemis."""
            try:
                print(f"Mensaje recibido de Artemis: {json.dumps(message, indent=2, ensure_ascii=False, default=str)}")
                
                datos_array = message.get('data', {}).get('datos', [])
                data = datos_array[0] if datos_array else {}
                if not data:
                    raise ValueError("El mensaje no contiene los datos requeridos")

                processor = DocumentProcessor(text_vectorizer)
                processor.document_uuid = data.get('archivo')
                processor.areas = data.get('areas', [])
                processor.nombre = data.get('nombre')
                processor.privacidad = data.get('privacidad')
                processor.creacion = data.get('creacion')
                processor.actualizacion = data.get('actualizacion')
                processor.correo = data.get('correo')
                processor.autor = data.get('autor')
                processor.ruta = data.get('ruta')
                processor.agente = data.get('agente')

                if not processor.document_uuid:
                    raise ValueError("El mensaje no contiene 'document_uuid' del documento")
                
                if processor.areas and isinstance(processor.areas, str):
                    processor.areas = processor.areas.split(',')

                if not processor.areas or not isinstance(processor.areas, list):
                    processor.areas = []
 
                if not processor.agente or not isinstance(processor.agente, str):
                    processor.agente = ""

                success = processor.download_file()
                if not success:
                    raise Exception("No se pudo descargar el archivo desde SFTP")

                processor.extraer_documento()
                if not processor.texto:
                    raise Exception("No se pudo extraer texto del documento")
 
                fragments = processor.split_text()
                if not fragments:
                    raise Exception("No se pudieron crear fragmentos de texto")
 
                processor.vectorize_fragments()

                if not processor.fragments:
                    raise Exception("No se pudieron vectorizar los fragmentos de texto")

                # Por si existe el documento primero lo tratamos de eliminar 
                processor.delete_document_from_elasticsearch()

                for i, fragment in enumerate(processor.fragments): 
                    print(f"Fragmento {i+1}/{len(processor.fragments)}: {json.dumps(fragment, indent=2, ensure_ascii=False)}")
                    processor.send_to_elasticsearch(fragment)

                # Guardar los keywords en Elasticsearch como metadato del documento
                processor.send_to_elasticsearch_keywords()

            except Exception as e:
                print(f"Error en el procesamiento del documento: {e}")
        
        if not artemis_connector.connect():
            raise Exception("No se pudo conectar a Artemis")

        subscription_id = artemis_connector.subscribe_to_queue(
            message_handler=handler, 
            subscription_id='tps-gestor-documental-movimientos'
        )

        print(f"Suscrito a la cola con el ID: {subscription_id}")
        

        # 5. Iniciar escucha (bloquea el hilo)
        try:
            artemis_connector.start_listening()
        except KeyboardInterrupt:
            print("Deteniendo...")
        finally:
            # 6. Desconectar al terminar
            artemis_connector.disconnect()
 

    except Exception as e:
        print(f"Error en la aplicación principal: {e}")

if __name__ == "__main__":
    import sys
    
    # Verificar si se pasa el argumento --bulk-load
    if len(sys.argv) > 1 and sys.argv[1] == "--bulk-load":
        print("Iniciando carga masiva de documentos desde init.jsonl")
        bulk_load_documents()
    else:
        main()

