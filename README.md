# Sistema de Procesamiento de Documentos# Document Extractor - Sistema de Extracción de Documentos



Sistema automatizado para procesar documentos desde SFTP, extraer contenido, fragmentar texto, vectorizar con modelos de embeddings e indexar en Elasticsearch.Un sistema Python completo para extraer automáticamente contenido de documentos **PDF**, **Word (.docx)** y **Excel (.xlsx)** con filtrado inteligente y **integración con Apache ActiveMQ Artemis** para procesamiento automático mediante colas de mensajes.



## Arquitectura## Características Principales



```### 📄 Extracción Completa de Documentos

Artemis MQ → SFTP Download → Document Extraction → LangChain Fragmentation → Vectorization → Elasticsearch Index- **Texto principal** con limpieza automática y reconstrucción de párrafos

```- **Tablas** preservando estructura de filas y columnas  

- **Metadatos** completos (autor, título, fechas de creación/modificación)

## Componentes

### 🧠 Filtrado Inteligente

- **Artemis MQ**: Recepción de mensajes JSON- **Páginas de portada** detectadas y omitidas automáticamente

- **SFTP**: Descarga de documentos del servidor remoto- **Tablas de contenido/índices** filtradas (líneas con números de página)

- **Document Extractor**: Extracción de contenido de PDF, Word, Excel- **Cabeceras y pies repetitivos** removidos de cada página

- **LangChain**: Fragmentación inteligente de texto- **Contenido duplicado** eliminado automáticamente

- **Vectorization**: Generación de embeddings multilingües (384 dimensiones)

- **Elasticsearch**: Indexación con soporte para búsqueda vectorial### 🔄 Integración Artemis MQ

- **Recepción de mensajes JSON** para procesamiento automático

## Instalación- **Conector STOMP** con reconexión automática

- **Estructura modular** en carpeta `/artemis`

```bash- **Solo recepción** - no envía mensajes de respuesta

pip install -r requirements.txt

```### 📊 Procesamiento por Tipo

| Tipo | Biblioteca | Capacidades |

## Configuración|------|------------|-------------|

| **PDF** | PyMuPDF + Camelot | Texto OCR + Tablas complejas + Metadatos |

Los archivos de configuración están en cada módulo:| **Word** | python-docx | Párrafos nativos + Tablas + Propiedades |

- `artemis/config/artemis_config.ini`| **Excel** | openpyxl | Múltiples hojas + Rangos automáticos + Metadatos |

- `sftp/config/sftp_config.ini`  

- `elasticsearch_connector/config/elasticsearch_config.ini`## 📁 Estructura del Proyecto

- `langchain/config/langchain_config.ini`

```

## Usodocument-extractor/

├── 📄 document_extractor.py    # Motor principal de extracción

### Prueba con documento real├── 📄 main.py                  # Interfaz de línea de comandos

```bash├── 📄 artemis_main.py          # Punto de entrada Artemis

python test_real_document.py├── 📁 artemis/                 # Módulo completo Artemis

```│   ├── connector.py            # Conector principal

│   ├── config_utils.py         # Utilidades de configuración

### Aplicación principal│   ├── config/                 # Archivos de configuración

```bash│   ├── examples/               # Ejemplos de uso

python main_application.py --test-document archivo.pdf│   ├── logs/                   # Logs del sistema

```│   └── results/                # Resultados de procesamiento

├── 📁 demo_files_tps/         # Archivos de prueba

## Estructura de Mensajes└── 📄 requirements.txt        # Dependencias

```

```json

{## 🚀 Instalación Rápida

  "documento_uuid": "archivo.pdf",

  "is_public": true,### Opción 1: Setup Automático (Windows)

  "metadatos": {```cmd

    "titulo": "Título del documento",# Ejecutar el script de instalación automática

    "descripcion": "Descripción",setup.bat

    "tipo_documento": "pdf"```

  },

  "areas_public_ids": ["area1", "area2"]### Opción 2: Instalación Manual

}```cmd

```# 1. Crear entorno virtual

python -m venv .venv

## Servicios Requeridos

# 2. Activar entorno virtual

- Elasticsearch: `http://localhost:9200`.\.venv\Scripts\activate

- Apache ActiveMQ Artemis: `localhost:61616`

- Servidor SFTP configurado# 3. Si da error de política de ejecución:

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

## Logs

# 4. Volver a activar el entorno virtual

Los logs se centralizan en `logs/` con información de todos los componentes..\.venv\Scripts\activate

# 5. Instalar dependencias
pip install -r requirements.txt
```

### Solución de Problemas Comunes

#### Error: "la ejecución de scripts está deshabilitada"
```powershell
# Ejecutar este comando ANTES de activar el entorno virtual:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Luego activar normalmente:
.\.venv\Scripts\activate
```

#### Error: "python no reconocido"
```cmd
# Usar 'py' en lugar de 'python' en Windows:
py -m venv .venv
py main.py archivo.pdf
```

#### Error: "camelot not found"
```cmd
pip install camelot-py[cv]
# Si falla, instalar dependencias del sistema:
# https://camelot-py.readthedocs.io/en/master/user/install.html
```

## Uso del Programa

### Como Script Ejecutable
```cmd
# Activar entorno virtual primero
.\.venv\Scripts\activate

# Procesar archivos
python main.py documento.pdf
python main.py "C:\Documents\reporte.docx"
python main.py datos.xlsx
python main.py archivo.pdf > resultado.json

# Ver ayuda
python main.py --help
```

### Como Módulo Python
```python
from document_extractor import DocumentExtractor

# Crear extractor
extractor = DocumentExtractor()

# Procesar archivo
resultado = extractor.extraer_documento("ruta/al/archivo.pdf")

# Acceder a contenido
texto = resultado['contenido']['texto']
tablas = resultado['contenido']['tablas'] 
metadatos = resultado['metadatos']

print(f"Texto extraído: {len(texto)} caracteres")
print(f"Tablas encontradas: {len(tablas)}")
print(f"Autor: {metadatos.get('autor', 'N/A')}")
```

## 🔄 Integración con Artemis MQ

### Configuración Artemis
```cmd
# Editar configuración
artemis/config/artemis_config.ini

# Iniciar conector
python artemis_main.py
```

### Formato de Mensajes JSON
Envíe mensajes JSON a la cola `document.processing`:
```json
{
    "request_id": "doc_001",
    "file_path": "/ruta/al/documento.pdf",
    "options": {
        "extract_tables": true,
        "extract_metadata": true
    }
}
```

### Ejemplos Artemis
```cmd
# Receptor básico
python artemis/examples/simple_receiver.py

# Procesador avanzado con document_extractor
python artemis/examples/document_processor.py
```

### Demostración Completa
```cmd
# Crear archivos de ejemplo y procesarlos
python demo.py

# Prueba rápida con estadísticas
python prueba.py

# Ver todos los ejemplos de uso
python ejemplos.py

# Ejecutar tests unitarios
python tests.py
```

## Estructura de Salida

El extractor retorna un diccionario JSON estructurado:

```json
{
  "tipo_archivo": "pdf|docx|xlsx",
  "archivo": "nombre_archivo.ext",
  "metadatos": {
    "titulo": "Título del documento",
    "autor": "Autor del documento", 
    "fecha_creacion": "2024-01-15T10:30:00",
    "fecha_modificacion": "2024-01-20T14:45:00",
    "paginas": 25
  },
  "contenido": {
    "texto": "Texto principal limpio del documento...",
    "tablas": [
      {
        "indice": 1,
        "datos": [
          {"Producto": "A", "Ventas": "100", "Región": "Norte"},
          {"Producto": "B", "Ventas": "200", "Región": "Sur"}
        ],
        "filas": 2,
        "columnas": 3
      }
    ]
  }
}
```

## Archivos del Proyecto

```
chat-port-docxtract/
├── document_extractor.py    # Motor principal del extractor
├── main.py                  # Script ejecutable CLI
├── demo.py                  # Demostración con archivos de ejemplo
├── ejemplos.py              # Ejemplos de uso e integración  
├── prueba.py                # Prueba rápida de funcionalidad
├── tests.py                 # Suite de tests unitarios
├── requirements.txt         # Dependencias Python
├── setup.bat               # Instalador automático (Windows)
├── README.md               # Esta documentación
├── .gitignore              # Archivos ignorados por git
└── demo_files/             # Archivos de ejemplo generados
    ├── ejemplo.pdf
    ├── ejemplo.docx
    └── ejemplo.xlsx
```

## Casos de Uso Típicos

1. **Procesamiento de informes PDF empresariales**
   - Extraer texto principal sin cabeceras repetitivas
   - Obtener tablas financieras con estructura preservada

2. **Análisis de documentos Word corporativos**  
   - Contenido de propuestas y reportes
   - Tablas de datos técnicos

3. **Conversión de hojas Excel a formato estructurado**
   - Múltiples hojas de cálculo a JSON
   - Datos para análisis posterior

4. **Automatización de ingesta de documentos**
   - Pipeline de procesamiento masivo
   - Preparación de datos para IA/ML

5. **Sistema de búsqueda documental**
   - Indexación de contenido
   - Extracción de metadatos para clasificación

## Integración en Sistemas

### Ejemplo de Sistema de Cola de Mensajes
```python
from document_extractor import DocumentExtractor
import json

class SistemaProcesamiento:
    def __init__(self):
        self.extractor = DocumentExtractor()
    
    def procesar_desde_cola(self, ruta_archivo):
        """Procesa archivo desde sistema de mensajería."""
        try:
            resultado = self.extractor.extraer_documento(ruta_archivo)
            self.guardar_en_bd(resultado)
            self.notificar_exito(resultado['archivo'])
            return resultado
        except Exception as e:
            self.manejar_error(ruta_archivo, str(e))
            raise
    
    def guardar_en_bd(self, contenido):
        """Implementar lógica de base de datos."""
        pass
```

### Ejemplo de API REST
```python
from flask import Flask, request, jsonify
from document_extractor import DocumentExtractor

app = Flask(__name__)
extractor = DocumentExtractor()

@app.route('/extraer', methods=['POST'])
def extraer_documento():
    archivo = request.files['documento']
    resultado = extractor.extraer_documento(archivo)
    return jsonify(resultado)
```

## Testing y Desarrollo

```cmd
# Ejecutar todos los tests
python tests.py

# Test específico
python -m unittest tests.TestDocumentExtractor.test_tipos_soportados

# Desarrollo con archivos de ejemplo
python demo.py
python main.py demo_files/ejemplo.pdf
```

## Dependencias Principales

- **PyMuPDF (fitz)** `1.23.14` - Procesamiento de PDFs
- **python-docx** `1.1.0` - Documentos Word
- **openpyxl** `3.1.2` - Archivos Excel
- **camelot-py[cv]** `0.10.1` - Extracción de tablas PDF
- **pandas** `2.1.4` - Manipulación de datos

## Contribución

Para contribuir al proyecto:

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Este proyecto es de código abierto. Ver archivo LICENSE para detalles.

## Soporte

- **Documentación completa**: Este README
- **Ejemplos**: `python ejemplos.py`
- **Tests**: `python tests.py`  
- **Demostración**: `python demo.py`

---
**¡Listo para extraer contenido de cualquier documento!**
