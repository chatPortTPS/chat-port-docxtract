# Sistema de Procesamiento de Documentos

Sistema automatizado para procesar documentos desde SFTP, extraer contenido, fragmentar texto con LangChain, vectorizar e indexar en Elasticsearch.

## Arquitectura

```
Artemis MQ → SFTP → Extracción → Fragmentación (LangChain) → Vectorización → Elasticsearch
```

## Componentes Principales

- **Artemis MQ**: Recepción de mensajes JSON para procesamiento
- **SFTP**: Descarga de documentos del servidor remoto
- **Extracción**: Procesamiento de PDF, Word, Excel y PowerPoint
- **LangChain**: Fragmentación inteligente de texto
- **Vectorización**: Embeddings multilingües (384 dimensiones)
- **Elasticsearch**: Indexación con búsqueda vectorial

## Instalación

```bash
# Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

**Nota Windows**: Si hay error de ejecución de scripts:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Configuración

Archivos de configuración en cada módulo:
- `artemis/config_ar.py`
- `sftp/config_sftp.py`
- `elasticsearch_connector/config_es.py`
- `langchain/config_chain.py`
- `vectorization/config_vectors.py`

## Uso

### Ejecución Principal
```bash
python main.py
```

### Formato de Mensaje Artemis
```json
{
  "documento_uuid": "archivo.pdf",
  "is_public": true,
  "metadatos": {
    "titulo": "Título del documento",
    "descripcion": "Descripción",
    "tipo_documento": "pdf"
  },
  "areas_public_ids": ["area1", "area2"]
}
```

## Estructura del Proyecto

```
chat-port-docxtract/
├── main.py                      # Punto de entrada principal
├── config_utils.py              # Utilidades de configuración
├── artemis/                     # Módulo Artemis MQ
├── sftp/                        # Módulo SFTP
├── convert_document_text/       # Extracción de documentos
├── langchain/                   # Fragmentación de texto
├── vectorization/               # Generación de embeddings
├── elasticsearch_connector/     # Indexación Elasticsearch
├── keywords/                    # Extracción de palabras clave
├── docker-compose.yml           # Configuración Docker
└── requirements.txt             # Dependencias Python
```

## Tipos de Documentos Soportados

| Tipo | Módulo | Capacidades |
|------|--------|-------------|
| PDF | `pdf.py` | Texto + Tablas + Metadatos |
| Word | `word.py` | Párrafos + Tablas |
| Excel | `excel.py` | Múltiples hojas |
| PowerPoint | `ppt.py` | Texto de slides |

## Servicios Requeridos

- **Elasticsearch**: `localhost:9200`
- **Apache ActiveMQ Artemis**: `localhost:61616`
- **Servidor SFTP**: Configurado según `config_sftp.py`

## Docker

```bash
# Desarrollo
docker-compose -f docker-compose.dev.yml up -d

# Producción
docker-compose up -d
```

## Flujo de Procesamiento

1. **Recepción**: Artemis recibe mensaje JSON con UUID del documento
2. **Descarga**: SFTP descarga el archivo desde servidor remoto
3. **Extracción**: Se procesa según tipo (PDF/Word/Excel/PPT)
4. **Fragmentación**: LangChain divide el texto en chunks optimizados
5. **Vectorización**: Generación de embeddings para búsqueda semántica
6. **Indexación**: Almacenamiento en Elasticsearch con vectores
7. **Keywords**: Extracción opcional de palabras clave

## Logs

Los logs se almacenan en el directorio `logs/` con información de todos los componentes.

## Dependencias Principales

- `PyMuPDF` - Procesamiento de PDFs
- `python-docx` - Documentos Word
- `openpyxl` - Archivos Excel
- `python-pptx` - Presentaciones PowerPoint
- `langchain` - Fragmentación de texto
- `sentence-transformers` - Vectorización
- `elasticsearch` - Indexación y búsqueda
- `stomp.py` - Cliente Artemis

