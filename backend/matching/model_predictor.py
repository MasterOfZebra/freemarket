"""
Предсказание совпадений через обученную ML-модель
Этап 2: Интеграция ML в matching pipeline
"""

import os
import json
import logging
from typing import Dict, Optional
from pathlib import Path

try:
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from scipy import sparse as sp
    SCIPY_SPARSE_AVAILABLE = True
except Exception:
    sp = None  # type: ignore
    SCIPY_SPARSE_AVAILABLE = False

from backend.matching.train_model import ModelTrainer
from backend.matching.features_extractor import FeatureCalculator
from backend.matching.semantic_embedder import SemanticFeatureCalculator

logger = logging.getLogger(__name__)


class ModelPredictor:
    """Предсказание вероятности совпадения через ML-модель (Singleton)"""

    _instance = None
    _initialized = False

    def __new__(cls, model_dir: str = "backend/data/models"):
        """Singleton pattern для переиспользования модели"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_dir: str = "backend/data/models"):
        """
        Инициализация предсказателя (lazy-load)

        Args:
            model_dir: Директория с моделями
        """
        if self._initialized:
            return

        self.model_dir = Path(model_dir)
        self.trainer = ModelTrainer(model_dir=str(model_dir))
        self.is_loaded = False
        self.feature_names = None
        self.semantic_calculator = SemanticFeatureCalculator()

        # Попытка загрузить модель
        if self.trainer.load_model():
            self.is_loaded = True
            # Загрузить список признаков
            feature_columns_path = self.model_dir / "feature_columns.json"
            if feature_columns_path.exists():
                with open(feature_columns_path, 'r', encoding='utf-8') as f:
                    self.feature_names = json.load(f)
            logger.info("ModelPredictor: модель загружена успешно")
        else:
            logger.warning("ModelPredictor: модель не найдена. Используется fallback на rule-based.")

        self._initialized = True

    def predict(
        self,
        features: Dict[str, float],
        return_proba: bool = False
    ) -> float:
        """
        Предсказать вероятность совпадения

        Args:
            features: Словарь с признаками
            return_proba: Вернуть вероятность вместо бинарного предсказания

        Returns:
            Вероятность совпадения (0-1) или бинарное предсказание (0/1)
        """
        if not self.is_loaded:
            logger.warning("Модель не загружена. Возвращаю fallback score.")
            return self._fallback_score(features)

        # Подготовить признаки (использовать сохранённый список или базовый)
        if self.feature_names:
            feature_names = self.feature_names
        else:
            feature_names = [
                'equivalence_score',
                'language_similarity',
                'category_match',
                'synonym_ratio',
                'word_order_penalty',
                'contextual_bonus',
                'word_overlap',
                'text_length_diff',
            ]

        X = np.array([[features.get(name, 0.0) for name in feature_names]])

        # Если модель/скейлер не готовы — fallback
        if not self.is_loaded or self.trainer.model is None or self.trainer.scaler is None:
            logger.warning("Модель/скейлер недоступны. Возвращаю fallback score.")
            return self._fallback_score(features) if return_proba else float(self._fallback_score(features) >= self.get_threshold())

        # Масштабирование
        X_scaled = self.trainer.scaler.transform(X)

        # Безопасные предсказания
        has_proba = hasattr(self.trainer.model, "predict_proba")
        has_predict = hasattr(self.trainer.model, "predict")

        if return_proba:
            if not has_proba:
                logger.warning("predict_proba недоступен у модели. Возвращаю эвристическую вероятность (fallback).")
                return self._fallback_score(features)
            probs = self.trainer.model.predict_proba(X_scaled)
            probs = _to_ndarray(probs)
            proba = probs[0, 1]
            return float(proba)
        else:
            if not has_predict:
                logger.warning("predict недоступен у модели. Возвращаю бинаризацию fallback-скора.")
                return float(self._fallback_score(features) >= self.get_threshold())
            raw_pred = self.trainer.model.predict(X_scaled)
            raw_pred = _to_ndarray(raw_pred).ravel()
            prediction = raw_pred[0]
            return float(prediction)

    def _fallback_score(self, features: Dict[str, float]) -> float:
        """
        Fallback score если модель не загружена

        Использует простое правило на основе признаков
        """
        base_score = features.get('equivalence_score', 0.5)
        category_match = features.get('category_match', 0.5)
        word_overlap = features.get('word_overlap', 0.0)

        # Упрощённое правило
        score = (base_score * 0.5 + category_match * 0.3 + word_overlap * 0.2)
        return score

    def predict_batch(self, features_list: list[Dict[str, float]]) -> list[float]:
        """
        Предсказать для батча признаков

        Args:
            features_list: Список словарей с признаками

        Returns:
            Список вероятностей
        """
        if not self.is_loaded:
            return [self._fallback_score(f) for f in features_list]

        # Подготовить признаки
        feature_names = [
            'equivalence_score',
            'language_similarity',
            'category_match',
            'synonym_ratio',
            'word_order_penalty',
            'contextual_bonus',
            'word_overlap',
            'text_length_diff',
        ]

        X = np.array([[f.get(name, 0.0) for name in feature_names] for f in features_list])

        # Если модель/скейлер не готовы — fallback
        if not self.is_loaded or self.trainer.model is None or self.trainer.scaler is None:
            return [self._fallback_score(f) for f in features_list]

        # Масштабирование
        X_scaled = self.trainer.scaler.transform(X)

        # Предсказание с учётом возможного отсутствия predict_proba
        if not hasattr(self.trainer.model, "predict_proba"):
            logger.warning("predict_proba недоступен у модели. Использую бинаризацию predict() с вероятностью=1 для класса 1.")
            raw = self.trainer.model.predict(X_scaled)
            raw = _to_ndarray(raw).ravel()
            return [float(v) for v in raw]

        probas = self.trainer.model.predict_proba(X_scaled)
        probas = _to_ndarray(probas)[:, 1]
        return [float(p) for p in probas]

    def get_threshold(self) -> float:
        """Получить оптимальный порог"""
        return self.trainer.threshold

    def is_available(self) -> bool:
        """Проверить доступность модели"""
        return self.is_loaded


def extract_features_for_prediction(
    rule_based_result: Dict[str, float],
    text1: str,
    text2: str,
    category_match: float,
    predictor: Optional['ModelPredictor'] = None
) -> Dict[str, float]:
    """
    Извлечь признаки для предсказания из результата rule-based matching

    Args:
        rule_based_result: Результат EnhancedRuleBasedMatcher.compute_enhanced_score()
        text1: Первый текст
        text2: Второй текст
        category_match: Совпадение категорий (0.1-1.0)
        predictor: ModelPredictor instance для семантических признаков

    Returns:
        Словарь с признаками
    """
    # Базовые признаки из rule-based результата
    features = {
        'equivalence_score': rule_based_result.get('base_score', 0.5),
        'language_similarity': 0.5,  # Будет заменено из LanguageNormalizer
        'category_match': category_match,
        'synonym_ratio': 0.5,  # Будет заменено из нормализации
        'word_order_penalty': 0.0,
        'contextual_bonus': rule_based_result.get('contextual_bonus', 0.0),
    }

    # Дополнительные признаки
    features['word_overlap'] = FeatureCalculator.calculate_word_overlap(text1, text2)
    features['text_length_diff'] = FeatureCalculator.calculate_text_length_diff(text1, text2)

    # Добавляем семантические признаки если predictor доступен
    if predictor and predictor.semantic_calculator:
        features = predictor.semantic_calculator.add_semantic_features(
            features, text1, text2
        )

    return features


def combine_scores(
    rule_based_score: float,
    ml_score: float,
    semantic_score: float = 0.0,
    weights: Optional[Dict[str, float]] = None,
    normalize: bool = True
) -> float:
    """
    Комбинировать rule-based, ML и semantic scores с нормализацией

    Args:
        rule_based_score: Score от rule-based matcher (0-1)
        ml_score: Score от ML модели (0-1)
        semantic_score: Score от semantic embedder (0-1)
        weights: Весовые коэффициенты для каждого компонента
        normalize: Нормализовать результат

    Returns:
        Комбинированный score (0-1)
    """
    if weights is None:
        # По умолчанию: rule-based 30%, ML 40%, semantic 30%
        weights = {
            'rule_based': 0.3,
            'ml': 0.4,
            'semantic': 0.3
        }

    # Если semantic score не предоставлен, перераспределяем веса
    if semantic_score == 0.0:
        total_weight = weights['rule_based'] + weights['ml']
        if total_weight > 0:
            weights = {
                'rule_based': weights['rule_based'] / total_weight,
                'ml': weights['ml'] / total_weight,
                'semantic': 0.0
            }

    combined = (
        rule_based_score * weights['rule_based'] +
        ml_score * weights['ml'] +
        semantic_score * weights['semantic']
    )

    if normalize and weights['semantic'] > 0:
        # Нормализованная комбинация
        total_weight = sum(weights.values())
        combined = combined / total_weight

    return min(max(combined, 0.0), 1.0)


def combine_scores_legacy(
    rule_based_score: float,
    ml_score: float,
    ml_weight: float = 0.4,
    normalize: bool = True
) -> float:
    """
    Устаревшая версия combine_scores для обратной совместимости

    Args:
        rule_based_score: Score от rule-based matcher (0-1)
        ml_score: Score от ML модели (0-1)
        ml_weight: Вес ML score (0-1)
        normalize: Нормализовать результат

    Returns:
        Комбинированный score (0-1)
    """
    return combine_scores(
        rule_based_score,
        ml_score,
        semantic_score=0.0,
        weights={'rule_based': 1.0 - ml_weight, 'ml': ml_weight, 'semantic': 0.0},
        normalize=normalize
    )


def _to_ndarray(x):  # type: ignore[no-redef]
    """Безопасно привести к numpy.ndarray, поддерживая scipy.sparse."""
    if SCIPY_SPARSE_AVAILABLE and (sp is not None) and sp.issparse(x):
        # Используем .todense() чтобы избежать предупреждений type checker на .toarray()
        return np.asarray(x.todense())
    return np.asarray(x)


if __name__ == "__main__":
    # Пример использования
    logging.basicConfig(level=logging.INFO)

    predictor = ModelPredictor()

    if predictor.is_available():
        # Тестовые признаки
        test_features = {
            'equivalence_score': 0.85,
            'language_similarity': 0.9,
            'category_match': 1.0,
            'synonym_ratio': 0.8,
            'word_order_penalty': 0.05,
            'contextual_bonus': 0.05,
            'word_overlap': 0.95,
            'text_length_diff': 0.1,
        }

        proba = predictor.predict(test_features, return_proba=True)
        print(f"Вероятность совпадения: {proba:.4f}")
    else:
        print("Модель не доступна. Обучите модель через train_model.py")

