"""
Расчет комплексного скоринга для matching
Учитывает семантику, word overlap, стоимость и duration
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

try:
    from .language_normalization import get_normalizer
    from .vector_similarity import get_vector_sim
except ImportError:
    from language_normalization import get_normalizer
    from vector_similarity import get_vector_sim

logger = logging.getLogger(__name__)


class ScoreComponent(Enum):
    """Компоненты скоринга"""
    SEMANTIC_VECTOR = "semantic_vector"        # Векторная семантическая близость
    WORD_OVERLAP = "word_overlap"             # Перекрытие слов
    FUZZY_MATCH = "fuzzy_match"               # Fuzzy matching для опечаток
    COST_PRIORITY = "cost_priority"           # Приоритет по стоимости
    DURATION_PENALTY = "duration_penalty"      # Штраф за несовпадение duration


@dataclass
class MatchingScore:
    """Комплексный скор мэтчинга"""
    total_score: float
    components: Dict[ScoreComponent, float]
    is_match: bool
    explanation: str
    priority_rank: float  # Для сортировки результатов

    def __post_init__(self):
        # Автоматическое определение is_match
        if 'is_match' not in self.__dict__:
            self.is_match = self.total_score >= 0.5  # Базовый порог


class MatchingScorer:
    """
    Расчет комплексного скоринга для matching
    """

    # Весовые коэффициенты компонентов
    WEIGHTS = {
        ScoreComponent.SEMANTIC_VECTOR: 0.4,    # 40% - семантическая близость
        ScoreComponent.WORD_OVERLAP: 0.6,       # 60% - перекрытие слов
        ScoreComponent.COST_PRIORITY: 0.0,      # 0% - приоритет по стоимости (добавляется отдельно)
    }

    # Пороги для разных типов
    THRESHOLDS = {
        'same_category': 0.70,
        'cross_category': 0.50,
        'minimum_match': 0.40,
    }

    def __init__(self):
        self.normalizer = get_normalizer()
        self.vector_sim = get_vector_sim()

    def calculate_score(
        self,
        text_a: str,
        text_b: str,
        price_a: Optional[float] = None,
        price_b: Optional[float] = None,
        duration_a: Optional[str] = None,
        duration_b: Optional[str] = None,
        category_a: Optional[str] = None,
        category_b: Optional[str] = None,
        is_cross_category: bool = False
    ) -> MatchingScore:
        """
        Рассчитать комплексный скор мэтчинга

        Args:
            text_a, text_b: Тексты для сравнения
            price_a, price_b: Цены (для приоритета)
            duration_a, duration_b: Длительности (для временного обмена)
            category_a, category_b: Категории
            is_cross_category: Межкатегорийный обмен

        Returns:
            MatchingScore с итоговым скором и компонентами
        """
        components = {}

        # 1. Семантическая векторная близость
        if self.vector_sim.is_available():
            semantic_score = self.vector_sim.vector_similarity(text_a, text_b)
        else:
            # Fallback к обычной схожести
            semantic_score = self.normalizer.similarity_score(text_a, text_b)
        components[ScoreComponent.SEMANTIC_VECTOR] = semantic_score

        # 2. Word overlap
        overlap_score = self._calculate_word_overlap(text_a, text_b)
        components[ScoreComponent.WORD_OVERLAP] = overlap_score

        # 3. Fuzzy matching для опечаток
        fuzzy_score = self._calculate_fuzzy_match(text_a, text_b)
        components[ScoreComponent.FUZZY_MATCH] = fuzzy_score

        # 4. Приоритет по стоимости (если цены указаны)
        cost_priority = self._calculate_cost_priority(price_a, price_b)
        components[ScoreComponent.COST_PRIORITY] = cost_priority

        # 5. Штраф за несовпадение duration (если указаны)
        duration_penalty = self._calculate_duration_penalty(duration_a, duration_b)
        components[ScoreComponent.DURATION_PENALTY] = duration_penalty

        # Расчет итогового скора
        final_score = (
            self.WEIGHTS[ScoreComponent.SEMANTIC_VECTOR] * semantic_score +
            self.WEIGHTS[ScoreComponent.WORD_OVERLAP] * overlap_score +
            cost_priority  # Добавляем cost_priority напрямую
        )

        # Применение duration penalty
        final_score *= duration_penalty

        # Определение порога
        threshold = self.THRESHOLDS['cross_category'] if is_cross_category else self.THRESHOLDS['same_category']
        is_match = final_score >= threshold

        # Приоритет для сортировки (учитывает стоимость)
        priority_rank = final_score * (1.0 + cost_priority * 0.5)

        # Формирование объяснения
        explanation = self._generate_explanation(components, is_cross_category)

        return MatchingScore(
            total_score=final_score,
            components=components,
            is_match=is_match,
            explanation=explanation,
            priority_rank=priority_rank
        )

    def _calculate_word_overlap(self, text_a: str, text_b: str) -> float:
        """Расчет перекрытия слов"""
        try:
            words_a = set(self.normalizer.normalize(text_a).split())
            words_b = set(self.normalizer.normalize(text_b).split())

            if not words_a or not words_b:
                return 0.0

            intersection = words_a & words_b
            union = words_a | words_b

            # Jaccard similarity
            overlap = len(intersection) / len(union) if union else 0.0

            # Бонус за порядок слов (если много общих слов подряд)
            if len(intersection) >= 2:
                overlap *= 1.2

            return min(1.0, overlap)

        except Exception as e:
            logger.error(f"Error calculating word overlap: {e}")
            return 0.0

    def _calculate_fuzzy_match(self, text_a: str, text_b: str) -> float:
        """Fuzzy matching для опечаток"""
        try:
            from rapidfuzz import fuzz  # type: ignore
            if not text_a or not text_b:
                return 0.0
            # Ratio similarity
            ratio = fuzz.ratio(text_a.lower(), text_b.lower()) / 100.0

            # Token sort ratio (игнорирует порядок слов)
            token_sort = fuzz.token_sort_ratio(text_a.lower(), text_b.lower()) / 100.0

            # Token set ratio (игнорирует дубликаты и порядок)
            token_set = fuzz.token_set_ratio(text_a.lower(), text_b.lower()) / 100.0

            # Взвешенное среднее
            fuzzy_score = (ratio * 0.3 + token_sort * 0.3 + token_set * 0.4)

            return fuzzy_score

        except ImportError:
            logger.warning("rapidfuzz not available, using fallback fuzzy match")
            # Fallback к простой схожести
            return self.normalizer.similarity_score(text_a, text_b)
        except Exception as e:
            logger.error(f"Error in fuzzy matching: {e}")
            return 0.0

    def _calculate_cost_priority(self, price_a: Optional[float], price_b: Optional[float]) -> float:
        """Расчет приоритета по стоимости"""
        if price_a is None or price_b is None or price_a <= 0 or price_b <= 0:
            return 0.0

        try:
            # Относительная разница цен
            diff_ratio = abs(price_a - price_b) / max(price_a, price_b)

            # Приоритет: чем меньше разница, тем выше приоритет
            # Формула: 1 / (1 + diff_ratio) дает значение от 0 (большая разница) до 1 (точное совпадение)
            priority = 1.0 / (1.0 + diff_ratio)

            return priority

        except Exception as e:
            logger.error(f"Error calculating cost priority: {e}")
            return 0.0

    def _calculate_duration_penalty(self, duration_a: Optional[str], duration_b: Optional[str]) -> float:
        """Расчет штрафа за несовпадение duration"""
        if duration_a is None or duration_b is None:
            return 1.0  # Нет штрафа

        try:
            # Простое сравнение строк (можно улучшить парсинг)
            if duration_a.lower().strip() == duration_b.lower().strip():
                return 1.1  # Бонус за точное совпадение
            else:
                # Штраф за несовпадение
                return 0.9

        except Exception as e:
            logger.error(f"Error calculating duration penalty: {e}")
            return 1.0

    def _generate_explanation(self, components: Dict[ScoreComponent, float], is_cross_category: bool) -> str:
        """Генерация объяснения скоринга"""
        explanations = []

        semantic = components.get(ScoreComponent.SEMANTIC_VECTOR, 0)
        overlap = components.get(ScoreComponent.WORD_OVERLAP, 0)
        fuzzy = components.get(ScoreComponent.FUZZY_MATCH, 0)
        cost = components.get(ScoreComponent.COST_PRIORITY, 0)

        if semantic > 0.8:
            explanations.append("очень высокая семантическая близость")
        elif semantic > 0.6:
            explanations.append("хорошая семантическая близость")
        elif semantic > 0.4:
            explanations.append("средняя семантическая близость")

        if overlap > 0.7:
            explanations.append("значительное перекрытие слов")
        elif overlap > 0.4:
            explanations.append("умеренное перекрытие слов")

        if fuzzy > 0.8:
            explanations.append("высокая схожесть по fuzzy matching")

        if cost > 0.2:
            explanations.append("близкие цены (высокий приоритет)")
        elif cost < -0.2:
            explanations.append("значительная разница в ценах")

        if is_cross_category:
            explanations.append("межкатегорийный обмен")

        if not explanations:
            explanations.append("низкая общая схожесть")

        return "; ".join(explanations)


# Глобальный экземпляр scorer
_scorer: Optional[MatchingScorer] = None


def get_scorer() -> MatchingScorer:
    """Получить глобальный экземпляр scorer"""
    global _scorer
    if _scorer is None:
        _scorer = MatchingScorer()
    return _scorer


def calculate_matching_score(
    text_a: str,
    text_b: str,
    **kwargs
) -> MatchingScore:
    """Удобная функция для расчета скоринга"""
    return get_scorer().calculate_score(text_a, text_b, **kwargs)
