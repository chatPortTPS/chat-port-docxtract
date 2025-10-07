"""
Conector SFTP de Solo Lectura para Document Extractor
===================================================

Módulo para conectarse a servidores SFTP en modo de solo lectura
para descargar archivos y documentos para procesamiento automático.

"""

import logging
import os
import paramiko
import stat
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import hashlib
import posixpath

from .config_sftp import load_config

# Configurar logging
logger = logging.getLogger(__name__)

# Verificar dependencias
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    logger.warning("Módulo 'paramiko' no instalado. Ejecute: pip install paramiko")


class SftpConnector:
    """
    Conector de solo lectura para servidores SFTP usando protocolo SSH.
    
    SOLO OPERACIONES DE LECTURA:
    - Conectar y listar archivos/directorios
    - Descargar archivos del servidor remoto
    - Verificar información y metadatos de archivos
    
    NO PERMITE operaciones de escritura o modificación del servidor.
    """
    
    def __init__(self):
        """
        Inicializa el conector SFTP de solo lectura.
        
        """
        # Cargar configuración desde archivo
        self.config = load_config()

        if not self.config:
            raise RuntimeError("No se pudo cargar la configuración SFTP")
        
        print(self.config)

        # Usar parámetros proporcionados o valores de configuración
        self.hostname = self.config.get('connection').get('hostname', '127.0.0.1')
        self.port = self.config.get('connection').get('port', 22)
        self.username = self.config.get('connection').get('username', 'root')
        self.password = self.config.get('connection').get('password', 'root')
        self.timeout = self.config.get('connection').get('timeout', 30)
        self.connection_attempts = 0

        self.ssh_client = None
        self.sftp_client = None
        self.connected = False
                        
        logger.info(f"Inicializando conector SFTP de SOLO LECTURA para {self.hostname}:{self.port}")
        logger.info(f"Directorio de entrada configurado: {self.get_remote_input_path()}")

    def get_remote_input_path(self) -> str:
        """
        Obtiene la ruta del directorio de entrada remoto desde la configuración.
        
        Returns:
            Ruta del directorio de entrada remoto
        """
        directories_config = self.config.get('directories', {})
        return directories_config.get('remote_input_path', '/')
    
    def get_local_load_directory(self) -> str:
        """
        Obtiene la ruta del directorio local para la descarga de documentos.
        
        Returns:
            Ruta del directorio local para la descarga de documentos
        """
        directories_config = self.config.get('directories', {})
        return directories_config.get('local_load_directory', '/documentos_download')
    

    
    def get_remote_base_path(self) -> str:
        """
        Obtiene la ruta base remota desde la configuración.
        
        Returns:
            Ruta base remota
        """
        directories_config = self.config.get('directories', {})
        return directories_config.get('remote_base_path', '/')
    
 
    def _remote_join(*parts: str) -> str:
        # Siempre POSIX en SFTP
        return posixpath.join(*(str(p).replace("\\", "/") for p in parts))

    def _local_join(*parts: str) -> Path:
        return Path(*parts)


    def connect(self) -> bool:
        """
        Establece conexión con el servidor SFTP.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        if not PARAMIKO_AVAILABLE:
            logger.error("No se puede conectar: módulo paramiko no disponible")
            raise RuntimeError("Módulo paramiko no disponible, instale con: pip install paramiko para usar el conector SFTP")
        
        try:
            logger.info(f"Conectando a SFTP en {self.hostname}:{self.port}...")
            self.connection_attempts += 1
            
            # Crear cliente SSH
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Conectar SSH
            self.ssh_client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )
            
            # Crear cliente SFTP
            self.sftp_client = self.ssh_client.open_sftp()
            
            self.connected = True
            logger.info("Conexión SFTP establecida exitosamente")
            
            # Verificar directorio home
            try:
                home_dir = self.sftp_client.getcwd() or "/"
                logger.info(f"Directorio actual: {home_dir}")
            except Exception as e:
                logger.warning(f"No se pudo obtener directorio actual: {e}")
            
            return True
            
        except paramiko.AuthenticationException:
            logger.error("Error de autenticación: credenciales inválidas")
            raise RuntimeError("Error de autenticación: credenciales inválidas")
        except paramiko.SSHException as e:
            logger.error(f"Error SSH: {e}")
            raise RuntimeError(f"Error SSH: {e}")
        except Exception as e:
            logger.error(f"Error conectando a SFTP: {e}")
            raise RuntimeError(f"Error conectando a SFTP: {e}")


    def disconnect(self):
        """Desconecta del servidor SFTP."""
        try:
            if self.sftp_client:
                logger.info("Desconectando SFTP...")
                self.sftp_client.close()
                self.sftp_client = None
            
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
            
            self.connected = False
            logger.info("Desconectado de SFTP")
            
        except Exception as e:
            logger.error(f"Error desconectando: {e}")
            raise RuntimeError(f"Error desconectando al desconectar SFTP: {e}")


    def download_file(self, name_archivo: str) -> bool:
        """
        Descarga un archivo del servidor SFTP.

        Args:
            name_archivo: Nombre del archivo a descargar

        Returns:
            True si la descarga es exitosa
        """
        if not self.connected:
            logger.error("No conectado a SFTP")
            raise RuntimeError("No conectado a SFTP")
        
        try:

            remote_path = '/mnt/sgd_qa/' + name_archivo
            local_path  = '/documentos_download/' + name_archivo
 
            logger.info(f"Descargando: {remote_path} -> {local_path}")
            
            # Crear directorio local si no existe
            local_dir = Path(local_path).parent
            local_dir.mkdir(parents=True, exist_ok=True)
             
            # Obtener tamaño del archivo remoto
            remote_stat = self.sftp_client.stat(remote_path)

            if not remote_stat:
                logger.error(f"Error: Archivo no encontrado: {remote_path}")
                raise RuntimeError(f"Archivo no encontrado: {remote_path}")

            remote_size = remote_stat.st_size
            
            # Descargar archivo 
            self.sftp_client.get(remote_path, local_path)
               
            # Verificar tamaño local
            local_size = Path(local_path).stat().st_size
            
            if local_size != remote_size:
                logger.error(f"Error: Tamaños no coinciden. Remoto: {remote_size}, Local: {local_size}")
                raise RuntimeError(f"Error: Tamaños no coinciden. Remoto: {remote_size}, Local: {local_size}, el archivo puede estar corrupto")
             
            logger.info(f"Descarga completada: {local_size} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Error descargando archivo: {e}")
            raise RuntimeError(f"Error descargando archivo: {e}")
    


    def delete_local_directories(self):

        """
        Elimina todos los directorios locales.
        """ 
        try:
            local_dir = Path(self.get_local_load_directory())
            if local_dir.exists() and local_dir.is_dir():
                for item in local_dir.iterdir():
                    if item.is_dir():
                        item.rmdir()
                logger.info(f"Directorios locales eliminados: {self.get_local_load_directory()}")
            else:
                logger.warning(f"No se encontraron directorios para eliminar en: {self.get_local_load_directory()}")
        except Exception as e:
            logger.error(f"Error eliminando directorios locales: {e}")
            raise RuntimeError(f"Error eliminando directorios locales: {e}")
