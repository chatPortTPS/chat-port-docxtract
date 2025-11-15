"""
Conector Elasticsearch - Document Extractor
===========================================

Módulo simple para conectarse a Elasticsearch y guardar documentos en un índice.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from pathlib import Path

# Configurar logging básico
logger = logging.getLogger(__name__)

# Dependencias de Elasticsearch
try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import ConnectionError, NotFoundError, RequestError
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

from .config_es import load_config, get_connection_params


class ElasticsearchConnector:
    """
    Conector simple para Elasticsearch que solo guarda documentos en un índice.
    """
    
    def __init__(self):
        """
        Inicializa el conector Elasticsearch
        """
        if not ELASTICSEARCH_AVAILABLE:
            logger.error("Elasticsearch no está disponible. Instale con: pip install elasticsearch")
            # No lanzar excepción aquí, dejar que el servicio maneje el error
            self.es = None
            self.connected = False
            self.index_name = 'documents'
            return
        
        self.config = load_config()
        self.connection_params = get_connection_params()
        self.es = None
        self.connected = False
        
        # Obtener nombre del índice desde configuración
        self.index_name = self.config.get('index_name', 'tps-gestor-documental')
        self.index_name_keywords = self.index_name + '_keywords'
    

    def connect(self) -> bool:
        """
        Establece conexión con Elasticsearch
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            logger.info("Conectando a Elasticsearch...")
            self.es = Elasticsearch(**self.connection_params)
            
            # Verificar conexión
            if self.es.ping():
                self.connected = True
                logger.info("Conectado a Elasticsearch exitosamente")
                return True
            else:
                logger.error("No se pudo establecer conexión con Elasticsearch")
                return False
                
        except Exception as e:
            logger.error(f"Error al conectar con Elasticsearch: {e}")
            return False
    

    def disconnect(self):
        """Cierra la conexión con Elasticsearch"""
        if self.es:
            self.es.close()
            self.connected = False
            logger.info("Desconectado de Elasticsearch")


    def create_index_if_not_exists(self, mapping: Dict[str, Any] = None) -> bool:
        """
        Crea el índice si no existe con el mapping especificado
        
        Args:
            mapping: Mapping completo del índice (incluyendo settings y mappings)
            
        Returns:
            True si se creó o ya existía, False en caso contrario
        """
        if not self.connected:
            logger.error("No hay conexión con Elasticsearch")
            return False
        
        try:
            # Verificar si el índice ya existe
            if self.es.indices.exists(index=self.index_name):
                logger.info(f"El índice '{self.index_name}' ya existe")
                return True

            if not mapping:
                logger.error("No se proporcionó mapping para crear el índice")
                return False
            
            # Crear índice
            self.es.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Índice '{self.index_name}' creado exitosamente")

            return True
            
        except RequestError as e:
            logger.error(f"Error al crear índice '{self.index_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado al crear índice '{self.index_name}': {e}")
            return False
    

    def save_document(self, document: Dict[str, Any], doc_id: str = None) -> bool:
        """
        Guarda un documento en el índice de Elasticsearch
        
        Args:
            document: Contenido del documento a guardar
            doc_id: ID único del documento (opcional)
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        if not self.connected:
            logger.error("No hay conexión con Elasticsearch")
            return False
        
        try:
            # Agregar timestamp si no existe
            if 'processed_date' not in document['metadata']:
                document['metadata']['processed_date'] = datetime.now().isoformat()
            
            # Indexar documento
            if doc_id:
                # primero se intenta eliminar el documento si ya existe
                self.es.delete(index=self.index_name, id=doc_id, ignore=[404])

                response = self.es.index(index=self.index_name, id=doc_id, body=document)
        
            else:
                logger.error("No se proporcionó doc_id para el documento")
                return False
            
            logger.info(f"Documento guardado: {doc_id or response['_id']} en índice {self.index_name}")

            return response['result'] in ['created', 'updated']
            
        except Exception as e:
            logger.error(f"Error al guardar documento {doc_id}: {e}")
            return False
    
    def save_document_keywords(self, doc_id: str, ruta: str, titulo: str, keywords: List[Dict[str, Any]]) -> bool:
        """
        Guarda los keywords de un documento como metadato en Elasticsearch
        
        Args:
            doc_id: ID único del documento
            ruta: Ruta del documento
            titulo: Título del documento
            keywords: Lista de keywords a guardar
            
        Returns:
            True si se guardaron correctamente, False en caso contrario
        """
        if not self.connected:
            logger.error("No hay conexión con Elasticsearch")
            return False
        
        try: 
            
            # Antes de guardar se debe eliminar el documento si ya existe para evitar duplicados
            self.es.delete(index=self.index_name_keywords, id=doc_id, ignore=[404])

            # Preparar cuerpo de actualización
            document = {
                "ruta": ruta,
                "titulo": titulo,
                "documento": doc_id,
                "keywords": keywords, 
                "fecha": datetime.now().isoformat()
            }

            # Actualizar el documento con los keywords
            response = self.es.index(index=self.index_name_keywords, id=doc_id, body=document)
            
            logger.info(f"Keywords guardados para documento {doc_id} en índice {self.index_name_keywords}")

            return response['result'] == 'created'
            
        except NotFoundError:
            logger.error(f"Documento {doc_id} no encontrado en índice {self.index_name_keywords}")
            return False
        except Exception as e:
            logger.error(f"Error al guardar keywords para documento {doc_id}: {e}")
            return False

    def __enter__(self):
        """Context manager entry"""
        if not self.connected:
            self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
