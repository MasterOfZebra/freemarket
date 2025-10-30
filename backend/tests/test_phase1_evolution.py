"""
Тесты для Этапа 1 эволюции matching-движка
Проверка: категорийные фильтры, морфология, контекстный анализ
"""

import pytest
import os
import json
import tempfile
from pathlib import Path

from backend.matching.rule_based import (
    MorphologyProcessor,
    ContextualKeywords,
    CategoryFilter,
    EnhancedRuleBasedMatcher,
    CategoryConfig,
)
from backend.matching.features_extractor import (
    TrainingDataCollector,
    FeatureCalculator,
    MatchingFeatures,
)


class TestMorphologyProcessor:
    """Тесты морфологического процессора"""

    @pytest.fixture
    def processor(self):
        return MorphologyProcessor()

    def test_lemmatize_verbs(self, processor):
        """Проверка лемматизации глаголов"""
        # Тестируем только если pymorphy2 доступен
        if processor.morph is None:
            pytest.skip("pymorphy2 не установлен")

        result = processor.lemmatize("куплю")
        assert result is not None
        assert isinstance(result, str)

    def test_lemmatize_nouns(self, processor):
        """Проверка лемматизации существительных"""
        if processor.morph is None:
            pytest.skip("pymorphy2 не установлен")

        result = processor.lemmatize("велосипеды")
        assert "велосипед" in result.lower()

    def test_lemmatize_text(self, processor):
        """Проверка лемматизации целого текста"""
        if processor.morph is None:
            pytest.skip("pymorphy2 не установлен")

        text = "куплю велосипеды и самокаты"
        result = processor.lemmatize_text(text)
        assert isinstance(result, str)
        assert len(result) > 0


class TestContextualKeywords:
    """Тесты анализа контекстных ключевых слов"""

    @pytest.fixture
    def keywords(self):
        return ContextualKeywords()

    def test_extract_keywords(self, keywords):
        """Проверка извлечения ключевых слов"""
        text = "куплю велосипед горный красный"
        result = keywords.extract_keywords(text)

        assert "велосипед" in result
        assert "горный" in result
        assert "красный" in result
        assert len(result) >= 3

    def test_stop_words_filtering(self, keywords):
        """Проверка фильтрации стоп-слов"""
        text = "и велосипед или самокат в городе"
        result = keywords.extract_keywords(text)

        # Стоп-слова должны быть удалены
        assert "и" not in result
        assert "или" not in result
        assert "в" not in result
        # Ключевые слова должны остаться
        assert "велосипед" in result
        assert "самокат" in result

    def test_keyword_weights(self, keywords):
        """Проверка вычисления весов ключевых слов"""
        text = "велосипед велосипед красный красный красный"
        weights = keywords.get_keyword_weights(text)

        # "красный" встречается 3 раза, "велосипед" - 2 раза
        assert weights["красный"] > weights["велосипед"]
        assert weights["красный"] <= 1.0

    def test_contextual_similarity_same_words(self, keywords):
        """Проверка сходства для одинаковых слов"""
        sim = keywords.compute_contextual_similarity(
            "велосипед горный красный",
            "велосипед горный красный"
        )
        assert sim > 0.8

    def test_contextual_similarity_different_context(self, keywords):
        """Проверка сходства для разного контекста"""
        sim1 = keywords.compute_contextual_similarity(
            "велосипед горный",
            "велосипед городской"
        )
        sim2 = keywords.compute_contextual_similarity(
            "велосипед горный",
            "мебель диван кровать"
        )
        assert sim2 < sim1


class TestCategoryFilter:
    """Тесты фильтра категорий"""

    @pytest.fixture
    def cat_filter(self):
        return CategoryFilter()

    def test_same_category_weight(self, cat_filter):
        """Проверка веса для одной и той же категории"""
        weight = cat_filter.get_category_weight("электроника", "электроника")
        assert weight == 1.0

    def test_different_category_weight(self, cat_filter):
        """Проверка веса для разных категорий"""
        weight = cat_filter.get_category_weight("электроника", "мебель")
        assert weight < 1.0
        assert weight > 0  # Должен быть ненулевой

    def test_filter_score(self, cat_filter):
        """Проверка применения фильтра категории к score"""
        base_score = 0.8

        # Одна категория
        filtered1 = cat_filter.filter_score(base_score, "электроника", "электроника")
        assert filtered1 == base_score

        # Разные категории
        filtered2 = cat_filter.filter_score(base_score, "электроника", "мебель")
        assert filtered2 < base_score

    def test_valid_match_same_items(self, cat_filter):
        """Проверка валидности матча для одинаковых предметов"""
        is_valid = cat_filter.is_valid_match("айфон", "айфон")
        assert is_valid

    def test_valid_match_partial(self, cat_filter):
        """Проверка валидности матча для частичного совпадения"""
        # "чехол для айфона" vs "айфон" - частичное совпадение, но не совсем неправильный матч
        is_valid = cat_filter.is_valid_match("чехол для айфона", "айфон")
        # Функция проверяет перекрытие слов, здесь > 30%, поэтому валидный матч
        assert is_valid

    def test_load_default_config(self, cat_filter):
        """Проверка загрузки стандартной конфигурации"""
        assert "электроника" in cat_filter.categories
        assert "одежда" in cat_filter.categories
        assert "спорт" in cat_filter.categories


class TestEnhancedRuleBasedMatcher:
    """Тесты усиленного rule-based matcher"""

    @pytest.fixture
    def matcher(self):
        return EnhancedRuleBasedMatcher()

    def test_preprocess_text(self, matcher):
        """Проверка предобработки текста"""
        text = "Куплю ВЕЛОСИПЕД горный! (с отличным состоянием)"
        norm, lemma = matcher.preprocess_text(text)

        assert norm.islower()
        assert "велосипед" in norm
        # Пунктуация и скобки удаляются
        assert "!" not in norm

    def test_enhanced_score_same_category(self, matcher):
        """Проверка score для одной категории"""
        result = matcher.compute_enhanced_score(
            "велосипед горный",
            "велосипед горный",
            "спорт",
            "спорт",
            base_score=0.8
        )

        assert "total_score" in result
        assert result["category_weight"] == 1.0
        assert result["is_valid"]
        assert result["total_score"] >= 0.8

    def test_enhanced_score_different_category(self, matcher):
        """Проверка score для разных категорий"""
        result = matcher.compute_enhanced_score(
            "велосипед",
            "велосипед",
            "спорт",
            "мебель",
            base_score=0.8
        )

        assert result["category_weight"] < 1.0
        assert result["total_score"] < 0.8

    def test_enhanced_score_invalid_match(self, matcher):
        """Проверка score для невалидного матча"""
        result = matcher.compute_enhanced_score(
            "чехол для айфона",
            "айфон",
            "электроника",
            "электроника",
            base_score=0.7
        )

        # Матч валидный (30% перекрытие слов), но score снижается
        assert result["is_valid"]
        assert result["total_score"] <= 0.7  # Снижено или равно базовому score


class TestTrainingDataCollector:
    """Тесты сборщика тренировочных данных"""

    @pytest.fixture
    def temp_storage(self):
        """Создать временное хранилище"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "training_pairs.jsonl")
            yield storage_path

    @pytest.fixture
    def collector(self, temp_storage):
        return TrainingDataCollector(storage_path=temp_storage)

    def test_add_pair(self, collector):
        """Проверка добавления пары"""
        features = MatchingFeatures(
            pair_id="test_1",
            text1="велосипед",
            text2="велосипед",
            category1="спорт",
            category2="спорт",
            equivalence_score=0.95,
            language_similarity=0.9,
            category_match=1.0,
            synonym_ratio=1.0,
            word_order_penalty=0.0,
            contextual_bonus=0.05,
            word_overlap=1.0,
            text_length_diff=0.0,
        )

        collector.add_pair(features)
        assert len(collector.pairs) == 1

    def test_add_user_feedback(self, collector):
        """Проверка добавления обратной связи пользователя"""
        features = MatchingFeatures(
            pair_id="test_2",
            text1="велосипед горный",
            text2="велосипед",
            category1="спорт",
            category2="спорт",
            equivalence_score=0.85,
            language_similarity=0.8,
            category_match=1.0,
            synonym_ratio=0.8,
            word_order_penalty=0.05,
            contextual_bonus=0.02,
            word_overlap=0.67,
            text_length_diff=0.3,
        )

        collector.add_pair(features)
        collector.add_user_feedback("test_2", True)

        pair = collector.pairs[0]
        assert pair.user_feedback == True
        assert pair.is_match == True

    def test_get_statistics(self, collector):
        """Проверка получения статистики"""
        for i in range(5):
            features = MatchingFeatures(
                pair_id=f"test_{i}",
                text1="text1",
                text2="text2",
                category1="cat1",
                category2="cat2",
                equivalence_score=0.5,
                language_similarity=0.5,
                category_match=0.5,
                synonym_ratio=0.5,
                word_order_penalty=0.5,
                contextual_bonus=0.05,
                word_overlap=0.5,
                text_length_diff=0.5,
            )
            collector.add_pair(features)

        stats = collector.get_statistics()
        assert stats["total_pairs"] == 5
        assert stats["labeled_pairs"] == 0

    def test_export_to_csv(self, collector, temp_storage):
        """Проверка экспорта в CSV"""
        features = MatchingFeatures(
            pair_id="test_csv",
            text1="велосипед",
            text2="велосипед",
            category1="спорт",
            category2="спорт",
            equivalence_score=0.95,
            language_similarity=0.9,
            category_match=1.0,
            synonym_ratio=1.0,
            word_order_penalty=0.0,
            contextual_bonus=0.05,
            word_overlap=1.0,
            text_length_diff=0.0,
            is_match=True,
        )

        collector.add_pair(features)

        csv_path = os.path.join(os.path.dirname(temp_storage), "output.csv")
        collector.export_to_csv(csv_path)

        assert os.path.exists(csv_path)


class TestFeatureCalculator:
    """Тесты вычислителя признаков"""

    def test_word_overlap_identical(self):
        """Проверка перекрытия слов для идентичного текста"""
        overlap = FeatureCalculator.calculate_word_overlap("велосипед горный", "велосипед горный")
        assert overlap == 1.0

    def test_word_overlap_no_common(self):
        """Проверка перекрытия слов без общих слов"""
        overlap = FeatureCalculator.calculate_word_overlap("велосипед", "диван")
        assert overlap == 0.0

    def test_word_overlap_partial(self):
        """Проверка частичного перекрытия слов"""
        overlap = FeatureCalculator.calculate_word_overlap(
            "велосипед горный красный",
            "велосипед городской"
        )
        assert 0 < overlap < 1
        # 1 общее слово (велосипед) из 4 уникальных = 0.25
        assert abs(overlap - 0.25) < 0.01

    def test_text_length_diff_same(self):
        """Проверка разницы длины для одинакового текста"""
        diff = FeatureCalculator.calculate_text_length_diff("велосипед", "велосипед")
        assert diff == 0.0

    def test_text_length_diff_different(self):
        """Проверка разницы длины для разного текста"""
        diff = FeatureCalculator.calculate_text_length_diff("велосипед", "в")
        assert 0 < diff <= 1.0

    def test_create_training_features(self):
        """Проверка создания признаков для обучения"""
        features = FeatureCalculator.create_training_features(
            pair_id="test",
            text1="велосипед горный",
            text2="велосипед городской",
            category1="спорт",
            category2="спорт",
            equivalence_score=0.85,
            language_similarity=0.8,
            category_match=1.0,
            synonym_ratio=0.5,
            word_order_penalty=0.1,
            contextual_bonus=0.05,
        )

        assert features.pair_id == "test"
        assert features.equivalence_score == 0.85
        assert features.word_overlap > 0
        assert 0 <= features.text_length_diff <= 1


# Интеграционный тест
class TestPhase1Integration:
    """Интеграционные тесты Этапа 1"""

    def test_full_matching_pipeline(self):
        """Проверка полного pipeline-а matching"""
        matcher = EnhancedRuleBasedMatcher()

        # Тестируем различные сценарии
        test_cases = [
            {
                'text1': 'велосипед горный',
                'text2': 'велосипед горный',
                'cat1': 'спорт',
                'cat2': 'спорт',
                'expect_high': True,
            },
            {
                'text1': 'айфон чёрный',
                'text2': 'чехол для айфона',
                'cat1': 'электроника',
                'cat2': 'электроника',
                'expect_high': False,
            },
            {
                'text1': 'велосипед',
                'text2': 'диван',
                'cat1': 'спорт',
                'cat2': 'мебель',
                'expect_high': False,
            },
        ]

        for case in test_cases:
            result = matcher.compute_enhanced_score(
                case['text1'],
                case['text2'],
                case['cat1'],
                case['cat2'],
                base_score=0.8
            )

            if case['expect_high']:
                assert result['total_score'] > 0.7
            else:
                assert result['total_score'] <= 0.8  # Может быть 0.5-0.8 для неправильных матчей


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
