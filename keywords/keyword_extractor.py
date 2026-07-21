import os
import sys
import spacy
from collections import Counter
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from pathlib import Path

# Importar el gestor de modelo compartido
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_model import get_shared_model

from .config_keywords import load_config
 
class KeywordExtractor:

    def __init__(self, model_spacy=None, model_sentence_transformers=None, stopwords_file=None):
        """
        Inicializa el extractor de keywords y entidades.
        
        Parámetros
        ----------
        text : str, opcional
            Texto a procesar (mantenido por compatibilidad).
        model_spacy : str, opcional
            Nombre del modelo spaCy. Si no se proporciona, se lee desde la configuración.
        model_sentence_transformers : str, opcional
            Nombre del modelo SentenceTransformer. Si no se proporciona, se lee desde la configuración.
        stopwords_file : str, opcional
            Ruta al archivo de stopwords. Si no se proporciona, se lee desde la configuración.
        """

        # Cargar configuración
        config = load_config()
        
        # Obtener configuración desde parámetros o config
        self.model_spacy = model_spacy or config['model_spacy']
        self.model_sentence_transformers = model_sentence_transformers or config['model_sentence_transformers']
        
        # Cargar stopwords desde archivo
        stopwords_path = stopwords_file or config['stopwords_file']
        stopwords_es = self._load_stopwords(stopwords_path)
        
        # Inicializar modelos
        self.nlp = spacy.load(self.model_spacy)
        
        # Obtener el modelo compartido (se reutiliza si ya fue cargado)
        self.embedding_model = get_shared_model(model_name=self.model_sentence_transformers)
        self.kw_model = KeyBERT(model=self.embedding_model)
        
        self._vectorizer = CountVectorizer(
            ngram_range=(1, 2),
            stop_words=stopwords_es,
            min_df=1
        )
    
    def _load_stopwords(self, stopwords_path):
        """
        Carga stopwords desde un archivo de texto.
        
        Parámetros
        ----------
        stopwords_path : str
            Ruta al archivo de stopwords (una palabra por línea).
            
        Retorna
        -------
        list[str]
            Lista de stopwords en minúsculas.
        """
        # Si es ruta relativa, buscar desde la raíz del proyecto
        if not os.path.isabs(stopwords_path):
            # Obtener la ruta raíz del proyecto (2 niveles arriba desde este archivo)
            project_root = Path(__file__).parent.parent
            stopwords_path = project_root / stopwords_path
        
        try:
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                stopwords = [line.strip().lower() for line in f if line.strip()]
            return stopwords
        except FileNotFoundError:
            print(f"Advertencia: No se encontró el archivo de stopwords en {stopwords_path}. Usando lista vacía.")
            return []

    def get_entidades(self, labels_target=None, texto="", k=10):
        """
        Extrae entidades nombradas (NER) desde un texto utilizando spaCy.

        El método procesa un fragmento de texto y retorna las entidades
        reconocidas por el modelo NER. De forma opcional, permite filtrar
        las entidades por tipo (label). Si no se especifican labels,
        se retornan todas las entidades detectadas.

        Parámetros
        ----------
        labels_target : list[str] | None, opcional
            Lista de etiquetas NER a considerar (por ejemplo: ["ORG", "GPE", "DATE"]).
            Si es None, se retornan todas las entidades detectadas.
        texto : str
            Fragmento de texto a procesar.
        k : int, opcional
            Número máximo de entidades a retornar, ordenadas por frecuencia
            de aparición en el texto. Por defecto es 10.

        Retorna
        -------
        list[str]
            Lista de entidades normalizadas (minúsculas), sin duplicados,
            ordenadas por frecuencia descendente.

        Notas
        -----
        - El método depende exclusivamente del modelo NER de spaCy cargado
        previamente (por ejemplo, ``es_core_news_md`` o ``es_core_news_lg``).
        - Si una entidad no es reconocida por el modelo, no será incluida
        en el resultado.
        - No se aplica ningún proceso de normalización semántica adicional
        ni reglas de dominio.
        """
        
        # Procesar el texto con spaCy
        doc = self.nlp(texto)

        # Lista para almacenar las entidades extraídas
        entidades = []

        # Recorrer todas las entidades detectadas por el modelo NER
        for ent in doc.ents:

            # Filtrar por labels si se especifican; de lo contrario, aceptar todas
            if labels_target is None or ent.label_ in labels_target:

                # Normalizar el texto de la entidad (trim + minúsculas)
                entidades.append(ent.text.strip().lower())

        # Contar la frecuencia de aparición de cada entidad
        conteo = Counter(entidades)

        # Retornar las k entidades más frecuentes
        return [ent for ent, _ in conteo.most_common(k)]


    def get_keywords_keybert_documento(
        self,
        texto: str,
        k: int = 10
    ):
        """
        Extrae palabras/frases clave a nivel DOCUMENTO usando KeyBERT
        + vectorizer explícito.
        """

        texto_prefijado = "passage: " + texto

        keywords = self.kw_model.extract_keywords(
            texto_prefijado,
            vectorizer=self._vectorizer, 
            top_n=k,
            use_mmr=False,
            diversity=0.5
        )

        return [kw for kw, score in keywords]