"""
Векторная семантическая близость на базе sentence-transformers
Используется для глубокого понимания смысла текста
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    logging.warning(f"Vector similarity dependencies not available: {e}")
    SentenceTransformer = None
    np = None
    cosine_similarity = None

logger = logging.getLogger(__name__)


class VectorSimilarity:
    """
    Векторная семантическая близость с использованием предобученных моделей
    """

    # Конфигурация моделей
    MODELS = {
        'multilingual': 'paraphrase-multilingual-MiniLM-L12-v2',  # Легкая мультиязычная
        'distiluse': 'distiluse-base-multilingual-cased-v2',      # Более точная, но тяжелая
    }

    def __init__(
        self,
        model_name: str = 'multilingual',
        cache_dir: Optional[str] = None,
        enable_cache: bool = True
    ):
        """
        Инициализация векторного similarity

        Args:
            model_name: Название модели ('multilingual', 'distiluse')
            cache_dir: Директория для кэширования модели
            enable_cache: Включить кэширование результатов
        """
        self.model_name = model_name
        self.enable_cache = enable_cache
        self._cache: Dict[Tuple[str, str], float] = {}
        self._model = None

        if SentenceTransformer is None:
            logger.warning("sentence-transformers not available, vector similarity disabled")
            return

        # Настройка кэша модели
        if cache_dir is None:
            cache_dir = os.getenv('SENTENCE_TRANSFORMERS_HOME', './models')

        os.environ['SENTENCE_TRANSFORMERS_HOME'] = cache_dir

        try:
            model_path = self.MODELS.get(model_name, model_name)
            logger.info(f"Loading sentence transformer model: {model_path}")
            self._model = SentenceTransformer(model_path, cache_folder=cache_dir)
            logger.info("Vector similarity model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load vector similarity model: {e}")
            self._model = None

    def _encode_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        """Кодирование текстов в векторы"""
        if self._model is None:
            return None

        try:
            return self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            return None

    def vector_similarity(self, text_a: str, text_b: str) -> float:
        """
        Рассчитать семантическую близость между двумя текстами

        Args:
            text_a: Первый текст
            text_b: Второй текст

        Returns:
            Схожесть от 0.0 до 1.0 (1.0 = идентичные по смыслу)
        """
        if self._model is None:
            logger.warning("Vector model not available, returning 0.0")
            return 0.0

        if not text_a or not text_b:
            return 0.0

        # Проверка кэша
        cache_key = (text_a, text_b)
        if self.enable_cache and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Кодирование текстов
            embeddings = self._encode_texts([text_a, text_b])

            if embeddings is None:
                return 0.0

            # Косинусная схожесть
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

            # Нормализация в диапазон 0-1
            similarity = max(0.0, min(1.0, similarity))

            # Кэширование
            if self.enable_cache:
                self._cache[cache_key] = similarity

            return float(similarity)

        except Exception as e:
            logger.error(f"Error calculating vector similarity: {e}")
            return 0.0

    def batch_similarity(self, text_pairs: List[Tuple[str, str]]) -> List[float]:
        """
        Пакетный расчет схожести для нескольких пар

        Args:
            text_pairs: Список пар (text_a, text_b)

        Returns:
            Список схожести для каждой пары
        """
        if self._model is None:
            return [0.0] * len(text_pairs)

        try:
            all_texts = []
            pair_indices = []

            # Собираем все уникальные тексты
            text_to_idx = {}
            for i, (text_a, text_b) in enumerate(text_pairs):
                if text_a not in text_to_idx:
                    text_to_idx[text_a] = len(text_to_idx)
                    all_texts.append(text_a)
                if text_b not in text_to_idx:
                    text_to_idx[text_b] = len(text_to_idx)
                    all_texts.append(text_b)
                pair_indices.append((text_to_idx[text_a], text_to_idx[text_b]))

            # Кодируем все тексты
            embeddings = self._encode_texts(all_texts)
            if embeddings is None:
                return [0.0] * len(text_pairs)

            # Рассчитываем схожести
            similarities = []
            for idx_a, idx_b in pair_indices:
                if idx_a < len(embeddings) and idx_b < len(embeddings):
                    sim = cosine_similarity([embeddings[idx_a]], [embeddings[idx_b]])[0][0]
                    similarities.append(max(0.0, min(1.0, float(sim))))
                else:
                    similarities.append(0.0)

            return similarities

        except Exception as e:
            logger.error(f"Error in batch similarity calculation: {e}")
            return [0.0] * len(text_pairs)

    def is_available(self) -> bool:
        """Проверка доступности векторной модели"""
        return self._model is not None


# Глобальный экземпляр для использования в приложении
_vector_sim: Optional[VectorSimilarity] = None


def get_vector_sim() -> VectorSimilarity:
    """Получить глобальный экземпляр векторного similarity"""
    global _vector_sim
    if _vector_sim is None:
        model_name = os.getenv('VECTOR_MODEL', 'multilingual')
        cache_dir = os.getenv('VECTOR_CACHE_DIR')
        _vector_sim = VectorSimilarity(
            model_name=model_name,
            cache_dir=cache_dir,
            enable_cache=True
        )
    return _vector_sim


def vector_similarity(text_a: str, text_b: str) -> float:
    """Удобная функция для расчета векторной схожести"""
    return get_vector_sim().vector_similarity(text_a, text_b)
