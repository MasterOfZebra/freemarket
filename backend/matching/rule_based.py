"""
Усиленный rule-based matching движок
Этап 1: Категорийные фильтры, лемматизация, контекстный анализ
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

try:
    import pymorphy2
    PYMORPHY_AVAILABLE = True
except ImportError:
    PYMORPHY_AVAILABLE = False
    logging.warning("pymorphy2 not installed. Install with: pip install pymorphy2")

logger = logging.getLogger(__name__)


@dataclass
class CategoryConfig:
    """Конфигурация категории с весами"""
    name: str
    weight: float = 1.0
    key_terms: List[str] = None

    def __post_init__(self):
        if self.key_terms is None:
            self.key_terms = []


class MorphologyProcessor:
    """Морфологический процессор на основе pymorphy2"""

    def __init__(self):
        if PYMORPHY_AVAILABLE:
            self.morph = pymorphy2.MorphAnalyzer()
        else:
            self.morph = None
            logger.warning("pymorphy2 не доступен. Лемматизация отключена.")

    def lemmatize(self, word: str) -> str:
        """Получить лемму слова"""
        if not self.morph:
            return word.lower()

        try:
            parsed = self.morph.parse(word)[0]
            return parsed.normal_form
        except Exception as e:
            logger.error(f"Ошибка при лемматизации '{word}': {e}")
            return word.lower()

    def lemmatize_text(self, text: str) -> str:
        """Лемматизировать весь текст"""
        if not self.morph:
            return text.lower()

        words = text.split()
        lemmas = [self.lemmatize(word) for word in words]
        return ' '.join(lemmas)

    def get_pos(self, word: str) -> str:
        """Получить часть речи"""
        if not self.morph:
            return "UNKNOWN"

        try:
            parsed = self.morph.parse(word)[0]
            return str(parsed.tag.POS)
        except Exception:
            return "UNKNOWN"


class ContextualKeywords:
    """Анализ контекстных ключевых слов"""

    def __init__(self, min_phrase_length: int = 3):
        self.min_phrase_length = min_phrase_length
        self.stop_words = {
            'и', 'или', 'не', 'в', 'на', 'с', 'по', 'для', 'к', 'от', 'как',
            'это', 'то', 'что', 'которые', 'который', 'которая'
        }

    def extract_keywords(self, text: str) -> List[str]:
        """Извлечь ключевые слова из текста"""
        words = text.lower().split()
        keywords = [w.strip('.,!?;:') for w in words if w.strip('.,!?;:') not in self.stop_words]
        return keywords

    def get_keyword_weights(self, text: str) -> Dict[str, float]:
        """Получить веса ключевых слов (частота + важность)"""
        keywords = self.extract_keywords(text)

        freq = {}
        for kw in keywords:
            freq[kw] = freq.get(kw, 0) + 1

        if freq:
            max_freq = max(freq.values())
            return {kw: count / max_freq for kw, count in freq.items()}

        return {}

    def compute_contextual_similarity(self, text1: str, text2: str) -> float:
        """Вычислить сходство с учётом контекста"""
        weights1 = self.get_keyword_weights(text1)
        weights2 = self.get_keyword_weights(text2)

        if not weights1 or not weights2:
            return 0.0

        common_keys = set(weights1.keys()) & set(weights2.keys())

        if not common_keys:
            return 0.0

        similarity = sum(weights1[k] * weights2[k] for k in common_keys)

        total_unique = len(set(weights1.keys()) | set(weights2.keys()))
        if total_unique > 0:
            similarity /= total_unique

        return min(similarity, 1.0)


class CategoryFilter:
    """Фильтр категорий для улучшения matching точности"""

    def __init__(self, config_path: Optional[str] = None):
        self.categories = {}
        self.contextual = ContextualKeywords()

        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        else:
            self._load_default_config()

    def _load_default_config(self):
        """Загрузить стандартную конфигурацию категорий"""
        self.categories = {
            'электроника': CategoryConfig(
                'электроника',
                weight=1.0,
                key_terms=['телефон', 'айфон', 'самсунг', 'чехол', 'зарядка', 'ноутбук',
                          'планшет', 'монитор', 'клавиатура', 'мышь', 'наушники']
            ),
            'одежда': CategoryConfig(
                'одежда',
                weight=1.0,
                key_terms=['куртка', 'пальто', 'платье', 'рубашка', 'брюки', 'юбка',
                          'свитер', 'пуховик', 'ботинки', 'туфли', 'кроссовки']
            ),
            'спорт': CategoryConfig(
                'спорт',
                weight=1.0,
                key_terms=['велосипед', 'самокат', 'скейтборд', 'коньки', 'лыжи',
                          'мяч', 'ракетка', 'гантели', 'штанга', 'спортивный']
            ),
            'мебель': CategoryConfig(
                'мебель',
                weight=1.0,
                key_terms=['стол', 'стул', 'кровать', 'диван', 'шкаф', 'полка',
                          'тумбочка', 'кресло', 'мебель', 'ящик']
            ),
        }

    def _load_config(self, config_path: str):
        """Загрузить конфигурацию из JSON файла"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for cat_name, cat_data in data.items():
                    self.categories[cat_name] = CategoryConfig(**cat_data)
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфигурации категорий: {e}")
            self._load_default_config()

    def get_category_weight(self, category1: str, category2: str) -> float:
        """Получить вес совпадения категорий"""
        cat1 = category1.lower().strip()
        cat2 = category2.lower().strip()

        if cat1 == cat2:
            return 1.0

        cat1_config = self.categories.get(cat1)
        cat2_config = self.categories.get(cat2)

        if cat1_config and cat2_config:
            cat_types = set()
            cat_types.add(cat1)
            cat_types.add(cat2)

            if len(cat_types) == 2:
                return 0.1

        return 0.5

    def filter_score(self, score: float, category1: str, category2: str) -> float:
        """Применить фильтр категории к score"""
        weight = self.get_category_weight(category1, category2)
        return score * weight

    def is_valid_match(self, text1: str, text2: str, min_score: float = 0.5) -> bool:
        """Проверить валидность матча на основе контекста"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if words1 < words2 or words2 < words1:
            overlap = len(words1 & words2) / min(len(words1), len(words2)) if min(len(words1), len(words2)) > 0 else 0

            if overlap < 0.3:
                return False

        return True


class EnhancedRuleBasedMatcher:
    """Усиленный rule-based matcher"""

    def __init__(self, use_morphology: bool = True, category_config_path: Optional[str] = None):
        self.morphology = MorphologyProcessor() if use_morphology and PYMORPHY_AVAILABLE else None
        self.category_filter = CategoryFilter(category_config_path)
        self.contextual = ContextualKeywords()

        logger.info("EnhancedRuleBasedMatcher инициализирован")
        if self.morphology:
            logger.info("  ✓ Морфологический анализ включен")
        logger.info("  ✓ Фильтр категорий включен")
        logger.info("  ✓ Контекстный анализ включен")

    def preprocess_text(self, text: str) -> Tuple[str, str]:
        """Предобработка текста"""
        normalized = text.lower().strip()
        for char in '.,!?;:-–—':
            normalized = normalized.replace(char, ' ')
        normalized = ' '.join(normalized.split())

        lemmatized = normalized
        if self.morphology:
            lemmatized = self.morphology.lemmatize_text(normalized)

        return normalized, lemmatized

    def compute_enhanced_score(
        self,
        text1: str,
        text2: str,
        category1: str,
        category2: str,
        base_score: float = 0.5
    ) -> Dict[str, float]:
        """Вычислить улучшенный score"""
        result = {
            'base_score': base_score,
            'category_weight': 1.0,
            'contextual_bonus': 0.0,
            'is_valid': True,
            'total_score': base_score
        }

        category_weight = self.category_filter.get_category_weight(category1, category2)
        result['category_weight'] = category_weight

        norm1, _ = self.preprocess_text(text1)
        norm2, _ = self.preprocess_text(text2)
        is_valid = self.category_filter.is_valid_match(norm1, norm2)
        result['is_valid'] = is_valid

        contextual_sim = self.contextual.compute_contextual_similarity(norm1, norm2)
        contextual_bonus = contextual_sim * 0.1
        result['contextual_bonus'] = contextual_bonus

        total = base_score * category_weight + contextual_bonus

        if not is_valid:
            total *= 0.7

        result['total_score'] = min(total, 1.0)

        return result


__all__ = [
    'MorphologyProcessor',
    'ContextualKeywords',
    'CategoryFilter',
    'EnhancedRuleBasedMatcher',
    'CategoryConfig'
]
