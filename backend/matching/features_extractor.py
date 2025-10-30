"""
Экстрактор признаков для ML-обучения
Этап 2: Подготовка данных для обучения моделей
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class MatchingFeatures:
    """Признаки пары для обучения"""
    pair_id: str
    text1: str
    text2: str
    category1: str
    category2: str

    # Основные признаки
    equivalence_score: float
    language_similarity: float
    category_match: float  # 1.0 if same, 0.5 if related, 0.1 if different
    synonym_ratio: float  # Доля синонимичных слов
    word_order_penalty: float  # Штраф за изменение порядка слов
    contextual_bonus: float

    # Производные признаки
    word_overlap: float
    text_length_diff: float

    # Метаданные
    is_match: Optional[bool] = None  # True/False для обучающих данных
    user_feedback: Optional[bool] = None  # Подтверждение пользователя
    match_quality: Optional[float] = None  # Качество матча (0-1)


class TrainingDataCollector:
    """Сборщик тренировочных данных"""

    def __init__(self, storage_path: str = "backend/data/training_pairs.jsonl"):
        self.storage_path = storage_path
        self.pairs: List[MatchingFeatures] = []
        self._load_existing_data()

    def _load_existing_data(self):
        """Загрузить существующие пары из файла"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.pairs.append(MatchingFeatures(**data))
            logger.info(f"Загружено {len(self.pairs)} пар обучающих данных")
        except FileNotFoundError:
            logger.info(f"Файл {self.storage_path} не найден. Начинаем с пустого набора.")
            self.pairs = []

    def add_pair(self, features: MatchingFeatures, save_immediately: bool = True):
        """Добавить пару в набор данных"""
        self.pairs.append(features)

        if save_immediately:
            self._save_pair(features)

        logger.debug(f"Добавлена пара: {features.pair_id}")

    def _save_pair(self, features: MatchingFeatures):
        """Сохранить пару в файл"""
        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(features), ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Ошибка при сохранении пары: {e}")

    def add_user_feedback(self, pair_id: str, is_match: bool):
        """Добавить обратную связь пользователя"""
        for pair in self.pairs:
            if pair.pair_id == pair_id:
                pair.user_feedback = is_match
                pair.is_match = is_match
                logger.info(f"Обратная связь добавлена для пары {pair_id}: {is_match}")
                self._save_pair(pair)
                return

        logger.warning(f"Пара {pair_id} не найдена")

    def get_labeled_data(self) -> Tuple[List[Dict], List[int]]:
        """
        Получить размеченные данные для обучения
        Возвращает (X, y) где X - признаки, y - метки (0/1)
        """
        X = []
        y = []

        for pair in self.pairs:
            if pair.is_match is not None:
                features_dict = self._extract_feature_vector(pair)
                X.append(features_dict)
                y.append(1 if pair.is_match else 0)

        logger.info(f"Подготовлено {len(X)} размеченных пар для обучения")
        logger.info(f"  Положительных примеров: {sum(y)}")
        logger.info(f"  Отрицательных примеров: {len(y) - sum(y)}")

        return X, y

    def _extract_feature_vector(self, features: MatchingFeatures) -> Dict[str, float]:
        """Извлечь вектор признаков из пары"""
        return {
            'equivalence_score': features.equivalence_score,
            'language_similarity': features.language_similarity,
            'category_match': features.category_match,
            'synonym_ratio': features.synonym_ratio,
            'word_order_penalty': features.word_order_penalty,
            'contextual_bonus': features.contextual_bonus,
            'word_overlap': features.word_overlap,
            'text_length_diff': features.text_length_diff,
        }

    def get_statistics(self) -> Dict:
        """Получить статистику по собранным данным"""
        total = len(self.pairs)
        labeled = sum(1 for p in self.pairs if p.is_match is not None)
        matches = sum(1 for p in self.pairs if p.is_match == True)
        non_matches = sum(1 for p in self.pairs if p.is_match == False)

        return {
            'total_pairs': total,
            'labeled_pairs': labeled,
            'matches': matches,
            'non_matches': non_matches,
            'labeling_percentage': (labeled / total * 100) if total > 0 else 0,
        }

    def export_to_csv(self, output_path: str):
        """Экспортировать данные в CSV для анализа"""
        import csv

        if not self.pairs:
            logger.warning("Нет данных для экспорта")
            return

        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'pair_id', 'text1', 'text2', 'category1', 'category2',
                    'equivalence_score', 'language_similarity', 'category_match',
                    'synonym_ratio', 'word_order_penalty', 'contextual_bonus',
                    'word_overlap', 'text_length_diff', 'is_match', 'user_feedback'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for pair in self.pairs:
                    writer.writerow(asdict(pair))

            logger.info(f"Данные экспортированы в {output_path}")
        except Exception as e:
            logger.error(f"Ошибка при экспорте: {e}")


class FeatureCalculator:
    """Вычислитель признаков"""

    @staticmethod
    def calculate_word_overlap(text1: str, text2: str) -> float:
        """Вычислить перекрытие слов"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def calculate_text_length_diff(text1: str, text2: str) -> float:
        """
        Вычислить различие в длине текстов (0-1)
        0 = одинаковая длина
        1 = очень разная длина
        """
        len1 = len(text1)
        len2 = len(text2)

        max_len = max(len1, len2)
        if max_len == 0:
            return 0.0

        diff = abs(len1 - len2) / max_len
        return min(diff, 1.0)

    @staticmethod
    def calculate_synonym_ratio(synonyms: List[Tuple[str, str]]) -> float:
        """
        Вычислить долю синонимичных слов
        synonyms: список кортежей (слово1, слово2)
        """
        if not synonyms:
            return 0.0

        return len(synonyms) / max(len(synonyms), 1)

    @staticmethod
    def create_training_features(
        pair_id: str,
        text1: str,
        text2: str,
        category1: str,
        category2: str,
        equivalence_score: float,
        language_similarity: float,
        category_match: float,
        synonym_ratio: float,
        word_order_penalty: float,
        contextual_bonus: float,
    ) -> MatchingFeatures:
        """Создать объект MatchingFeatures"""

        word_overlap = FeatureCalculator.calculate_word_overlap(text1, text2)
        text_length_diff = FeatureCalculator.calculate_text_length_diff(text1, text2)

        return MatchingFeatures(
            pair_id=pair_id,
            text1=text1,
            text2=text2,
            category1=category1,
            category2=category2,
            equivalence_score=equivalence_score,
            language_similarity=language_similarity,
            category_match=category_match,
            synonym_ratio=synonym_ratio,
            word_order_penalty=word_order_penalty,
            contextual_bonus=contextual_bonus,
            word_overlap=word_overlap,
            text_length_diff=text_length_diff,
        )


__all__ = [
    'MatchingFeatures',
    'TrainingDataCollector',
    'FeatureCalculator',
]
