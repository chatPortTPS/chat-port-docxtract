"""
Conector Artemis MQ
========================================

Módulo para conectarse a Apache ActiveMQ Artemis y recibir mensajes de colas
para el procesamiento automático de documentos.

"""

import json
import logging
import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime

# Configurar logging
logger = logging.getLogger(__name__)

# Dependencias de Artemis - se instalarán bajo demanda
try:
    import stomp
    STOMP_AVAILABLE = True
except ImportError:
    STOMP_AVAILABLE = False
    logger.warning("Módulo 'stomp.py' no instalado. Ejecute: pip install stomp.py")

from .config_ar import load_config

class ArtemisConnector:
    """
    Conector para Apache ActiveMQ Artemis usando protocolo STOMP.
    
    Maneja la conexión, suscripción a colas y procesamiento de mensajes
    para el sistema de extracción de documentos.
    """
    
    def __init__(self):
        """
        Inicializa el conector Artemis usando configuración centralizada.
        """

        # Cargar configuración centralizada
        artemis_config = load_config()
        
        self.host = artemis_config['host']
        self.port = artemis_config['port']
        self.username = artemis_config['username']
        self.password = artemis_config['password']
        self.virtual_host = artemis_config['virtual_host']
        
        # Configuración de reconexión
        self.max_reconnect_attempts = artemis_config['max_reconnect_attempts']
        self.reconnect_delay = artemis_config['reconnect_delay']
        
        # Cola por defecto para procesamiento de documentos
        self.queue = artemis_config['queue_document_processing']

        # Configuración de timeouts
        self.connection_timeout = artemis_config['connection_timeout']
        
        self.connection = None
        self.connected = False
        self.subscriptions = {}
        self.message_handlers = {}
        self.running = False
        
        # Estado de reconexión
        self.reconnect_attempts = 0
        
        logger.info(f"Inicializando conector Artemis para {self.host}:{self.port}")
    
    def connect(self) -> bool:
        """
        Establece conexión con el servidor Artemis.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        if not STOMP_AVAILABLE:
            logger.error("No se puede conectar: módulo stomp.py no disponible")
            raise RuntimeError("Módulo stomp.py no disponible, instale con: pip install stomp.py para usar el conector Artemis")
        
        try:
            logger.info(f"Conectando a Artemis en {self.host}:{self.port}...")
            
            # Crear conexión STOMP
            self.connection = stomp.Connection(
                host_and_ports=[(self.host, self.port)],
                heartbeats=(4000, 4000)  # 4 segundos de heartbeat
            )
            
            # Configurar listener para eventos de conexión
            self.connection.set_listener('', ArtemisMessageListener(self))
            
            # Conectar
            self.connection.connect(
                username=self.username,
                passcode=self.password,
                wait=True,
                headers={'host': self.virtual_host}
            )
            
            self.connected = True
            self.reconnect_attempts = 0
            logger.info("Conexión a Artemis establecida exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a Artemis: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconecta del servidor Artemis."""
        if self.connection and self.connected:
            try:
                logger.info("Desconectando de Artemis...")
                self.running = False
                
                # Desuscribirse de todas las colas
                for subscription_id in list(self.subscriptions.keys()):
                    self.unsubscribe(subscription_id)
                
                self.connection.disconnect()
                self.connected = False
                logger.info("Desconectado de Artemis")
                
            except Exception as e:
                logger.error(f"Error desconectando: {e}")
    
    def subscribe_to_queue(self, 
                          message_handler: Callable[[Dict[str, Any]], None],
                          subscription_id: Optional[str] = None) -> str:
        """
        Se suscribe a una cola para recibir mensajes.
        
        Args:
            message_handler: Función para procesar mensajes recibidos
            subscription_id: ID único de la suscripción (opcional)
            
        Returns:
            ID de la suscripción creada
        """
        if not self.connected:
            logger.error("No conectado a Artemis. Conéctese primero.")
            raise RuntimeError("No conectado a Artemis. Conéctese primero.")
        
        if subscription_id is None:
            subscription_id = f"sub_{self.queue}_{int(time.time())}"
        
        try:
            logger.info(f"Suscribiéndose a cola: {self.queue}")

            # Registrar handler de mensajes
            self.message_handlers[subscription_id] = message_handler
            
            # Suscribirse a la cola
            destination = self.queue
            self.connection.subscribe(
                destination=destination,
                id=subscription_id,
                ack='client-individual'  # ACK manual
            )
            
            self.subscriptions[subscription_id] = {
                'queue': self.queue,
                'destination': destination,
                'handler': message_handler,
                'created': datetime.now()
            }

            logger.info(f"Suscrito a {self.queue} con ID: {subscription_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Error suscribiéndose a {self.queue}: {e}")
            raise RuntimeError(f"Error suscribiéndose a {self.queue}: {e}")
    
    def unsubscribe(self, subscription_id: str):
        """
        Cancela la suscripción a una cola.
        
        Args:
            subscription_id: ID de la suscripción a cancelar
        """
        if subscription_id in self.subscriptions:
            try:
                logger.info(f"Cancelando suscripción: {subscription_id}")
                self.connection.unsubscribe(id=subscription_id)
                
                del self.subscriptions[subscription_id]
                if subscription_id in self.message_handlers:
                    del self.message_handlers[subscription_id]
                
                logger.info(f"Suscripción {subscription_id} cancelada")
                
            except Exception as e:
                logger.error(f"Error cancelando suscripción {subscription_id}: {e}")
                raise RuntimeError(f"Error cancelando suscripción {subscription_id}: {e}")
    

    def start_listening(self):
        """Inicia el loop de escucha de mensajes."""
        self.running = True
        logger.info("Iniciando escucha de mensajes...")
        
        try:
            while self.running and self.connected:
                time.sleep(1)  # Mantener el hilo vivo
                
                # Verificar conexión y reconectar si es necesario
                if not self.connected and self.running:
                    self._attempt_reconnect()
                    
        except KeyboardInterrupt:
            logger.info("Interrumpido por usuario")
        except Exception as e:
            logger.error(f"Error en loop de escucha: {e}")
        finally:
            self.running = False
    

    def _attempt_reconnect(self):
        """Intenta reconectar al servidor."""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Máximo número de intentos de reconexión alcanzado")
            return
        
        self.reconnect_attempts += 1
        logger.info(f"Intento de reconexión {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        time.sleep(self.reconnect_delay)
        
        if self.connect():
            # Re-suscribirse a las colas
            for sub_id, sub_info in list(self.subscriptions.items()):
                self.subscribe_to_queue(
                    sub_info['queue'],
                    sub_info['handler'],
                    sub_id
                )
    


class ArtemisMessageListener(stomp.ConnectionListener):
    """
    Listener para eventos de conexión y mensajes de Artemis.
    """
    
    def __init__(self, connector: ArtemisConnector):
        self.connector = connector
    
    def on_connected(self, frame):
        """Callback cuando se establece la conexión."""
        logger.info("Evento: Conectado a Artemis")
        self.connector.connected = True
    
    def on_disconnected(self):
        """Callback cuando se pierde la conexión."""
        logger.warning("Evento: Desconectado de Artemis")
        self.connector.connected = False
    
    def on_error(self, frame):
        """Callback para errores."""
        logger.error(f"Error de Artemis: {frame.body}")
    
    def on_message(self, frame):
        """
        Callback cuando se recibe un mensaje.
        
        Args:
            frame: Frame del mensaje STOMP
        """
        try:
            # Obtener información del mensaje
            subscription_id = frame.headers.get('subscription')
            message_id = frame.headers.get('message-id')
            destination = frame.headers.get('destination')
            
            logger.info(f"Mensaje recibido en {destination} (ID: {message_id})")
            
            # Deserializar mensaje
            try:
                message_data = json.loads(frame.body)
            except json.JSONDecodeError:
                message_data = {'raw_body': frame.body}
            
            # Preparar contexto del mensaje
            message_context = {
                'subscription_id': subscription_id,
                'message_id': message_id,
                'destination': destination,
                'headers': dict(frame.headers),
                'data': message_data,
                'timestamp': datetime.now(),
                'raw_frame': frame
            }
            
            # Llamar al handler registrado
            if subscription_id in self.connector.message_handlers:
                handler = self.connector.message_handlers[subscription_id]
                
                try:
                    handler(message_context)
                    
                    # ACK del mensaje si el handler no falló
                    self.connector.connection.ack(message_id, subscription_id)
                    logger.debug(f"Mensaje {message_id} procesado y confirmado")
                    
                except Exception as e:
                    logger.error(f"Error en handler de mensaje {message_id}: {e}")
                    # NACK del mensaje para reintento
                    self.connector.connection.nack(message_id, subscription_id)
            else:
                logger.warning(f"No hay handler para suscripción {subscription_id}")
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            raise RuntimeError(f"Error procesando mensaje: {e}")

