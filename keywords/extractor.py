"""
Extractor de Palabras Clave
===========================

Implementa múltiples algoritmos para extraer frases clave de documentos:
- TF-IDF (Term Frequency-Inverse Document Frequency)
- RAKE (Rapid Automatic Keyword Extraction)
- YAKE (Yet Another Keyword Extractor)
- KeyBERT (Keyword Extraction with BERT)
"""

import logging
from typing import List, Dict, Any, Optional
from collections import Counter
import re

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """Extractor de palabras clave que combina múltiples algoritmos."""

    def __init__(self, method: str = 'keybert', top_n: int = 10):
        """
        Inicializa el extractor de palabras clave.

        Args:
            method: Método a usar ('tfidf', 'rake', 'yake', 'keybert', 'all')
            top_n: Número de palabras clave a extraer
        """
        self.method = method.lower()
        self.top_n = top_n
        self.model = None

        # Inicializar el método seleccionado
        self._initialize_method()

    def _initialize_method(self):
        """Inicializa el método de extracción seleccionado."""
        try:
            if self.method == 'keybert':
                from keybert import KeyBERT
                logger.info("Inicializando KeyBERT...")
                self.model = KeyBERT()
                logger.info("KeyBERT inicializado correctamente")

            elif self.method == 'yake':
                import yake
                logger.info("Inicializando YAKE...")
                # Configuración de YAKE: lenguaje español, max 3 palabras por frase
                self.model = yake.KeywordExtractor(
                    lan="es",
                    n=3,  # Máximo de palabras por frase
                    dedupLim=0.9,
                    dedupFunc='seqm',
                    windowsSize=1,
                    top=self.top_n
                )
                logger.info("YAKE inicializado correctamente")

            elif self.method == 'rake':
                from rake_nltk import Rake
                logger.info("Inicializando RAKE...")
                self.model = Rake(language='spanish')
                logger.info("RAKE inicializado correctamente")

            elif self.method == 'tfidf':
                logger.info("TF-IDF será calculado on-demand (no requiere inicialización)")

            elif self.method == 'all':
                logger.info("Modo 'all' - todos los algoritmos serán usados")
                # Inicializar todos
                from keybert import KeyBERT
                import yake
                from rake_nltk import Rake

                self.keybert_model = KeyBERT()
                self.yake_model = yake.KeywordExtractor(
                    lan="es", n=3, dedupLim=0.9,
                    dedupFunc='seqm', windowsSize=1, top=self.top_n
                )
                self.rake_model = Rake(language='spanish')
                logger.info("Todos los modelos inicializados correctamente")
            else:
                raise ValueError(f"Método no reconocido: {self.method}")

        except ImportError as e:
            logger.error(f"Error al importar dependencias: {e}")
            logger.info("Asegúrate de instalar las dependencias necesarias")
            raise

    def extract_keywords(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrae palabras clave del texto usando el método configurado.

        Args:
            text: Texto del cual extraer palabras clave

        Returns:
            Lista de diccionarios con las palabras clave y sus scores
        """
        if not text or not text.strip():
            logger.warning("Texto vacío proporcionado")
            return []

        try:
            if self.method == 'keybert':
                return self._extract_with_keybert(text)
            elif self.method == 'yake':
                return self._extract_with_yake(text)
            elif self.method == 'rake':
                return self._extract_with_rake(text)
            elif self.method == 'tfidf':
                return self._extract_with_tfidf(text)
            elif self.method == 'all':
                return self._extract_with_all(text)
            else:
                raise ValueError(f"Método no soportado: {self.method}")

        except Exception as e:
            logger.error(f"Error extrayendo palabras clave: {e}")
            return []

    def _extract_with_keybert(self, text: str) -> List[Dict[str, Any]]:
        """Extrae palabras clave usando KeyBERT."""
        try:
            keywords = self.model.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 3),
                stop_words='spanish',
                top_n=self.top_n,
                diversity=0.5
            )

            return [
                {
                    'keyword': kw[0],
                    'score': float(kw[1]),
                    'method': 'keybert'
                }
                for kw in keywords
            ]
        except Exception as e:
            logger.error(f"Error en KeyBERT: {e}")
            return []

    def _extract_with_yake(self, text: str) -> List[Dict[str, Any]]:
        """Extrae palabras clave usando YAKE."""
        try:
            keywords = self.model.extract_keywords(text)

            return [
                {
                    'keyword': kw[0],
                    'score': float(kw[1]),  # En YAKE, menor score = mejor
                    'method': 'yake'
                }
                for kw in keywords
            ]
        except Exception as e:
            logger.error(f"Error en YAKE: {e}")
            return []

    def _extract_with_rake(self, text: str) -> List[Dict[str, Any]]:
        """Extrae palabras clave usando RAKE."""
        try:
            self.model.extract_keywords_from_text(text)
            keywords_with_scores = self.model.get_ranked_phrases_with_scores()

            # Tomar solo top_n
            top_keywords = keywords_with_scores[:self.top_n]

            return [
                {
                    'keyword': kw[1],
                    'score': float(kw[0]),
                    'method': 'rake'
                }
                for kw in top_keywords
            ]
        except Exception as e:
            logger.error(f"Error en RAKE: {e}")
            return []

    def _extract_with_tfidf(self, text: str) -> List[Dict[str, Any]]:
        """Extrae palabras clave usando TF-IDF simple."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            # Crear corpus de un solo documento (simplificado)
            vectorizer = TfidfVectorizer(
                max_features=self.top_n,
                ngram_range=(1, 3),
                stop_words='english'  # sklearn no tiene stopwords en español built-in
            )

            # Necesitamos al menos 2 documentos para TF-IDF
            # Dividimos el texto en párrafos para simular múltiples documentos
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

            if len(paragraphs) < 2:
                # Si hay un solo párrafo, lo dividimos en oraciones
                paragraphs = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

            if len(paragraphs) < 2:
                logger.warning("Texto muy corto para TF-IDF, retornando vacío")
                return []

            tfidf_matrix = vectorizer.fit_transform(paragraphs)
            feature_names = vectorizer.get_feature_names_out()

            # Obtener scores promedio de TF-IDF
            avg_scores = tfidf_matrix.mean(axis=0).A1
            top_indices = avg_scores.argsort()[-self.top_n:][::-1]

            return [
                {
                    'keyword': feature_names[idx],
                    'score': float(avg_scores[idx]),
                    'method': 'tfidf'
                }
                for idx in top_indices
            ]
        except Exception as e:
            logger.error(f"Error en TF-IDF: {e}")
            return []

    def _extract_with_all(self, text: str) -> List[Dict[str, Any]]:
        """Extrae palabras clave usando todos los métodos y combina resultados."""
        all_keywords = []

        # KeyBERT
        try:
            kb_keywords = self._extract_with_keybert_model(text)
            all_keywords.extend(kb_keywords)
        except Exception as e:
            logger.error(f"Error en KeyBERT (all mode): {e}")

        # YAKE
        try:
            yake_keywords = self._extract_with_yake_model(text)
            all_keywords.extend(yake_keywords)
        except Exception as e:
            logger.error(f"Error en YAKE (all mode): {e}")

        # RAKE
        try:
            rake_keywords = self._extract_with_rake_model(text)
            all_keywords.extend(rake_keywords)
        except Exception as e:
            logger.error(f"Error en RAKE (all mode): {e}")

        # TF-IDF
        try:
            tfidf_keywords = self._extract_with_tfidf(text)
            all_keywords.extend(tfidf_keywords)
        except Exception as e:
            logger.error(f"Error en TF-IDF (all mode): {e}")

        # Combinar y rankear por frecuencia de aparición
        keyword_counter = Counter([kw['keyword'].lower() for kw in all_keywords])

        # Crear resultado combinado
        combined = []
        seen = set()

        for kw in all_keywords:
            kw_lower = kw['keyword'].lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                combined.append({
                    'keyword': kw['keyword'],
                    'score': float(kw['score']),
                    'method': kw['method'],
                    'frequency': keyword_counter[kw_lower]
                })

        # Ordenar por frecuencia (cuántos métodos lo detectaron) y luego por score
        combined.sort(key=lambda x: (x['frequency'], x['score']), reverse=True)

        return combined[:self.top_n]

    def _extract_with_keybert_model(self, text: str) -> List[Dict[str, Any]]:
        """Helper para KeyBERT en modo 'all'."""
        keywords = self.keybert_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words='spanish',
            top_n=self.top_n,
            diversity=0.5
        )

        return [
            {
                'keyword': kw[0],
                'score': float(kw[1]),
                'method': 'keybert'
            }
            for kw in keywords
        ]

    def _extract_with_yake_model(self, text: str) -> List[Dict[str, Any]]:
        """Helper para YAKE en modo 'all'."""
        keywords = self.yake_model.extract_keywords(text)

        return [
            {
                'keyword': kw[0],
                'score': 1.0 - float(kw[1]),  # Invertir para que mayor sea mejor
                'method': 'yake'
            }
            for kw in keywords
        ]

    def _extract_with_rake_model(self, text: str) -> List[Dict[str, Any]]:
        """Helper para RAKE en modo 'all'."""
        self.rake_model.extract_keywords_from_text(text)
        keywords_with_scores = self.rake_model.get_ranked_phrases_with_scores()

        top_keywords = keywords_with_scores[:self.top_n]

        return [
            {
                'keyword': kw[1],
                'score': float(kw[0]),
                'method': 'rake'
            }
            for kw in top_keywords
        ]
