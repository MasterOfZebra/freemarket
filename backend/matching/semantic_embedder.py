 development
"""
Semantic Embedder для sentence embeddings (Этап 3)
Использует sentence-transformers для семантического сходства
"""

import logging
from typing import List, Tuple, Dict, Optional, Union
import numpy as np

try:
    from sentence_transformers import SentenceTransformer, util
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers не установлен. Установите: pip install sentence-transformers")

try:
    import fasttext
    FASTTEXT_AVAILABLE = True
except ImportError:
    FASTTEXT_AVAILABLE = False
    logging.warning("fasttext не установлен. Установите: pip install fasttext")

logger = logging.getLogger(__name__)


class SemanticEmbedder:
    """
    Генерация sentence embeddings для семантического сходства

    Поддерживает:
    - SentenceTransformer (multilingual-MiniLM)
    - FastText (быстрее, но менее точный)
    """

    def __init__(
        self,
        model_type: str = "sentence_transformer",
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        device: str = "cpu"
    ):
        """
        Инициализация embedder

        Args:
            model_type: "sentence_transformer" или "fasttext"
            model_name: Название модели
            device: "cpu" или "cuda"
        """
        self.model_type = model_type
        self.model_name = model_name
        self.device = device
        self.model = None
        self.embedding_dim = 384  # Для MiniLM

        if model_type == "sentence_transformer" and SENTENCE_TRANSFORMERS_AVAILABLE:
            self._init_sentence_transformer()
        elif model_type == "fasttext" and FASTTEXT_AVAILABLE:
            self._init_fasttext()
        else:
            logger.warning(f"Модель {model_type} недоступна. Используется заглушка.")
            self.model_type = "fallback"

    def _init_sentence_transformer(self):
        """Инициализация SentenceTransformer"""
        try:
            logger.info(f"Загрузка SentenceTransformer: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"SentenceTransformer загружен: dim={self.embedding_dim}")
        except Exception as e:
            logger.error(f"Ошибка загрузки SentenceTransformer: {e}")
            self.model_type = "fallback"

    def _init_fasttext(self):
        """Инициализация FastText"""
        try:
            logger.info(f"Загрузка FastText: {self.model_name}")
            self.model = fasttext.load_model(self.model_name)
            self.embedding_dim = self.model.get_dimension()
            logger.info(f"FastText загружен: dim={self.embedding_dim}")
        except Exception as e:
            logger.error(f"Ошибка загрузки FastText: {e}")
            self.model_type = "fallback"

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Генерация embeddings для списка текстов

        Args:
            texts: Список текстов

        Returns:
            Список векторов embeddings
        """
        if self.model_type == "fallback":
            # Заглушка: возвращает случайные векторы
            logger.debug(f"SemanticEmbedder.encode: заглушка для {len(texts)} текстов")
            return [[np.random.normal(0, 1) for _ in range(self.embedding_dim)] for _ in texts]

        try:
            if self.model_type == "sentence_transformer":
                embeddings = self.model.encode(texts, convert_to_numpy=True)
                return embeddings.tolist()

            elif self.model_type == "fasttext":
                embeddings = []
                for text in texts:
                    # Усреднение embeddings слов
                    words = text.lower().split()
                    if words:
                        word_vectors = [self.model.get_word_vector(word) for word in words]
                        avg_vector = np.mean(word_vectors, axis=0)
                    else:
                        avg_vector = np.zeros(self.embedding_dim)
                    embeddings.append(avg_vector)
                return embeddings

        except Exception as e:
            logger.error(f"Ошибка при генерации embeddings: {e}")
            return [[0.0] * self.embedding_dim for _ in texts]

    def similarity(self, text1: str, text2: str) -> float:
        """
        Вычислить семантическое сходство между двумя текстами

        Args:
            text1: Первый текст
            text2: Второй текст

        Returns:
            Косинусное сходство (0-1)
        """
        if self.model_type == "fallback":
            # Заглушка: случайное сходство
            return np.random.uniform(0.1, 0.9)

        try:
            embeddings = self.encode([text1, text2])
            emb1, emb2 = embeddings[0], embeddings[1]

            # Косинусное сходство
            similarity = util.cos_sim(emb1, emb2)
            return float(similarity)

        except Exception as e:
            logger.error(f"Ошибка при вычислении similarity: {e}")
            return 0.0

    def compute_semantic_features(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Вычислить semantic_similarity фичу для ML модели

        Args:
            text1: Первый текст
            text2: Второй текст

        Returns:
            Semantic similarity score (0-1)
        """
        return self.similarity(text1, text2)

    def batch_similarity(self, text_pairs: List[Tuple[str, str]]) -> List[float]:
        """
        Вычислить сходство для батча пар

        Args:
            text_pairs: Список пар (text1, text2)

        Returns:
            Список сходств
        """
        similarities = []
        for text1, text2 in text_pairs:
            sim = self.similarity(text1, text2)
            similarities.append(sim)
        return similarities

    def get_embedding_dim(self) -> int:
        """Получить размерность embeddings"""
        return self.embedding_dim

    def is_available(self) -> bool:
        """Проверить доступность модели"""
        return self.model_type != "fallback"


def get_semantic_similarity(text1: str, text2: str, model_type: str = "sentence_transformer") -> float:
    """
    Удобная функция для получения semantic similarity

    Args:
        text1: Первый текст
        text2: Второй текст
        model_type: Тип модели

    Returns:
        Semantic similarity (0-1)
    """
    embedder = SemanticEmbedder(model_type=model_type)
    return embedder.compute_semantic_features(text1, text2)


# Singleton instances для разных моделей
_embedder_instances = {}


def get_embedder(model_type: str = "sentence_transformer", model_name: Optional[str] = None) -> SemanticEmbedder:
    """
    Получить singleton instance embedder

    Args:
        model_type: Тип модели
        model_name: Название модели (опционально)

    Returns:
        SemanticEmbedder instance
    """
    key = f"{model_type}_{model_name or 'default'}"

    if key not in _embedder_instances:
        if model_name:
            _embedder_instances[key] = SemanticEmbedder(model_type=model_type, model_name=model_name)
        else:
            _embedder_instances[key] = SemanticEmbedder(model_type=model_type)

    return _embedder_instances[key]


class SemanticFeatureCalculator:
    """
    Вычислитель семантических признаков для ML модели
    """

    def __init__(self, embedder: Optional[SemanticEmbedder] = None):
        """
        Инициализация вычислителя

        Args:
            embedder: SemanticEmbedder instance (опционально)
        """
        self.embedder = embedder or get_embedder()

    def add_semantic_features(
        self,
        features: Dict[str, float],
        text1: str,
        text2: str
    ) -> Dict[str, float]:
        """
        Добавить семантические признаки к feature вектору

        Args:
            features: Исходный словарь признаков
            text1: Первый текст
            text2: Второй текст

        Returns:
            Обновленный словарь с semantic признаками
        """
        if not self.embedder.is_available():
            features['semantic_similarity'] = 0.0
            return features

        # Основное семантическое сходство
        semantic_sim = self.embedder.similarity(text1, text2)
        features['semantic_similarity'] = semantic_sim

        # Дополнительные признаки
        features['semantic_confidence'] = min(semantic_sim * 1.5, 1.0)  # Уверенность

        # Нормализованное сходство
        features['semantic_normalized'] = (semantic_sim - 0.5) * 2  # -1 to 1 scale

        return features

    def compute_semantic_score(
        self,
        rule_based_score: float,
        ml_score: float,
        text1: str,
        text2: str,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Вычислить hybrid score с семантикой

        Args:
            rule_based_score: Score от rule-based matcher
            ml_score: Score от ML модели
            text1: Первый текст
            text2: Второй текст
            weights: Весовые коэффициенты

        Returns:
            Hybrid score с семантикой
        """
        if weights is None:
            weights = {
                'rule_based': 0.3,
                'ml': 0.4,
                'semantic': 0.3
            }

        semantic_score = self.embedder.similarity(text1, text2)

        hybrid_score = (
            rule_based_score * weights['rule_based'] +
            ml_score * weights['ml'] +
            semantic_score * weights['semantic']
        )

        return min(max(hybrid_score, 0.0), 1.0)


if __name__ == "__main__":
    # Пример использования
    logging.basicConfig(level=logging.INFO)

    # Тест SentenceTransformer
    embedder = SemanticEmbedder(model_type="sentence_transformer")

    if embedder.is_available():
        # Тестовые тексты
        texts = ["велосипед горный красный", "самокат электрический", "велосипед городской"]
        embeddings = embedder.encode(texts)

        print(f"Embeddings shape: {np.array(embeddings).shape}")

        # Тест сходства
        sim1 = embedder.similarity("велосипед горный", "велосипед городской")
        sim2 = embedder.similarity("велосипед", "диван")

        print(f"Велосипеды похожи: {sim1:.3f}")
        print(f"Велосипед vs диван: {sim2:.3f}")

        # Тест с feature calculator
        calculator = SemanticFeatureCalculator(embedder)
        features = {'equivalence_score': 0.8}
        updated_features = calculator.add_semantic_features(features, texts[0], texts[1])

        print(f"Features with semantic: {updated_features}")
    else:
        print("Semantic embedder недоступен. Установите sentence-transformers:")
        print("pip install sentence-transformers")

