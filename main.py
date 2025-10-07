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

# Crear directorio de logs si no existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'document_processor.log'),
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

    def __init__(self):
        """Inicializa el procesador de documentos."""
        self.sftp_connector = None
        self.document_text_converter = None
        self.document_uuid = None
        self.texto = None
        self.splitter = None
        self.fragments = []
        self.vectorizer = None
        self.areas = ["Operaciones", "Seguridad"]
        self._initialize_components()


    def _initialize_components(self):
        """Inicializa los componentes disponibles."""
        self.sftp_connector = SftpConnector()
        self.document_text_converter = DocumentTextConverter()
        self.splitter = TextSplitter()
        self.vectorizer = TextVectorizer()
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
                "titulo": self.texto.get('metadatos', {}).get('titulo', ''),
                "autor": self.texto.get('metadatos', {}).get('autor', ''),
                "fecha_creacion": self.texto.get('metadatos', {}).get('fecha_creacion', ''),
                "fecha_modificacion": self.texto.get('metadatos', {}).get('fecha_modificacion', '')
            },

            "content_raw": fragment.get('text', ''),
            "title": self.texto.get('metadatos', {}).get('titulo', ''),
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
            success = self.es_connector.save_document(fragment)
            self.es_connector.disconnect()
            return success
        except Exception as e:
            print(f"Error enviando fragmento a Elasticsearch: {e}")
            return False

 

def main():
    
    try:
  
        def handler(message: Dict[str, Any]):
            """Maneja un mensaje recibido de Artemis."""
            try:
                processor = DocumentProcessor()
                
                processor.document_uuid = message.get('document_uuid')
                processor.areas = message.get('areas', [])
 
                if not processor.document_uuid:
                    raise ValueError("El mensaje no contiene 'document_uuid' del documento")
                
                if processor.areas is []:
                    raise ValueError("El mensaje no contiene 'areas' del documento")

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

            except Exception as e:
                print(f"Error en el procesamiento del documento: {e}")


        # Crear instancia del procesador
        artemis_connector = ArtemisConnector()
        artemis_connector.connect()

        artemis_connector.subscribe_to_queue(
            message_handler=handler, 
            subscription_id='tps-gestor-documental-movimientos'
        )

        artemis_connector.start_listening()
 

    except Exception as e:
        print(f"Error en la aplicación principal: {e}")
    
    

if __name__ == "__main__":
    main()

