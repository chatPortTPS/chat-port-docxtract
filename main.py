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
from elasticsearch_connector.connector import ElasticsearchConnector
from artemis import ArtemisConnector

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
        self.areas = None

        self.nombre = None
        self.privacidad = None
        self.creacion = None
        self.actualizacion = None
        self.correo = None
        self.autor = None
        self.ruta = None

        self._initialize_components()


    def _initialize_components(self):
        """Inicializa los componentes disponibles."""
        self.sftp_connector = SftpConnector()
        self.document_text_converter = DocumentTextConverter()
        self.splitter = TextSplitter()
        self.es_connector = ElasticsearchConnector()
 
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

    def extract_keywords(self) -> List[Dict[str, Any]]:
        """Extrae palabras clave del documento usando el algoritmo configurado."""
        if self.keyword_extractor is None:
            raise ValueError("KeywordExtractor no está disponible")

        texto_completo = self.texto.get('contenido', {}).get('texto', '')

        if not texto_completo:
            raise ValueError("No hay texto para extraer palabras clave")

        self.keywords = self.keyword_extractor.extract_keywords(texto_completo)
        logger.info(f"Palabras clave extraídas: {len(self.keywords)}")

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
                "keywords": self.keywords  # Agregar palabras clave extraídas
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
        
def main():
    
    try:

        # 1. Inicializar TextVectorizer (carga el modelo, puede tardar)
        text_vectorizer = TextVectorizer()

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

                if not processor.document_uuid:
                    raise ValueError("El mensaje no contiene 'document_uuid' del documento")
 
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
    main()

