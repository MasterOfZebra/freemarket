"""
Автоматический тюнинг порога для ML-модели
Этап 2: Оптимизация порога по F1-score
"""

import logging
from typing import Dict, Tuple
import numpy as np

try:
    from sklearn.metrics import f1_score, precision_score, recall_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class ThresholdTuner:
    """Оптимизация порога для бинарной классификации"""

    def __init__(self, metric: str = "f1"):
        """
        Инициализация тюнера

        Args:
            metric: Метрика для оптимизации ("f1", "precision", "recall", "f1_weighted")
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn не установлен")

        self.metric = metric
        self.best_threshold = 0.5
        self.best_score = 0.0

    def find_optimal_threshold(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray,
        threshold_range: Tuple[float, float] = (0.1, 0.9),
        step: float = 0.01
    ) -> Dict[str, float]:
        """
        Найти оптимальный порог

        Args:
            y_true: Истинные метки (0/1)
            y_proba: Вероятности предсказания
            threshold_range: Диапазон порогов для поиска
            step: Шаг поиска

        Returns:
            Словарь с оптимальным порогом и метриками
        """
        thresholds = np.arange(threshold_range[0], threshold_range[1] + step, step)
        best_threshold = 0.5
        best_score = 0.0
        best_metrics = {}

        for threshold in thresholds:
            y_pred = (y_proba >= threshold).astype(int)

            if self.metric == "f1":
                score = f1_score(y_true, y_pred)
            elif self.metric == "precision":
                score = precision_score(y_true, y_pred, zero_division=0)
            elif self.metric == "recall":
                score = recall_score(y_true, y_pred, zero_division=0)
            elif self.metric == "f1_weighted":
                # Баланс precision и recall
                prec = precision_score(y_true, y_pred, zero_division=0)
                rec = recall_score(y_true, y_pred, zero_division=0)
                score = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
            else:
                raise ValueError(f"Неизвестная метрика: {self.metric}")

            if score > best_score:
                best_score = score
                best_threshold = threshold
                best_metrics = {
                    'threshold': threshold,
                    'f1_score': f1_score(y_true, y_pred),
                    'precision': precision_score(y_true, y_pred, zero_division=0),
                    'recall': recall_score(y_true, y_pred, zero_division=0),
                }

        self.best_threshold = best_threshold
        self.best_score = best_score

        logger.info(f"Оптимальный порог: {best_threshold:.3f}")
        logger.info(f"  F1-score: {best_metrics['f1_score']:.4f}")
        logger.info(f"  Precision: {best_metrics['precision']:.4f}")
        logger.info(f"  Recall: {best_metrics['recall']:.4f}")

        return best_metrics

    def get_best_threshold(self) -> float:
        """Получить оптимальный порог"""
        return self.best_threshold

