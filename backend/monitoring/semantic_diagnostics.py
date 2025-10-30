"""
Semantic Diagnostics для обнаружения outliers и валидации
Этап 3.4: Мониторинг качества semantic matching
"""

import json
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime

try:
    import numpy as np
    import pandas as pd
    from sklearn.metrics import confusion_matrix, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from backend.matching.features_extractor import TrainingDataCollector
from backend.matching.semantic_embedder import get_embedder, SemanticFeatureCalculator
from backend.matching.rule_based import EnhancedRuleBasedMatcher
from backend.matching.model_predictor import ModelPredictor

logger = logging.getLogger(__name__)


class SemanticDiagnostics:
    """
    Диагностика semantic matching для обнаружения outliers и валидации
    """

    def __init__(
        self,
        collector: Optional[TrainingDataCollector] = None,
        output_dir: str = "backend/monitoring/reports"
    ):
        """
        Инициализация диагностики

        Args:
            collector: TrainingDataCollector с данными
            output_dir: Директория для отчётов
        """
        self.collector = collector or TrainingDataCollector()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Компоненты
        self.embedder = get_embedder()
        self.semantic_calculator = SemanticFeatureCalculator(self.embedder)
        self.matcher = EnhancedRuleBasedMatcher()
        self.predictor = ModelPredictor()

        logger.info("SemanticDiagnostics инициализирован")
        if self.embedder.is_available():
            logger.info("✓ Semantic embedder доступен")
        else:
            logger.warning("⚠ Semantic embedder недоступен")

    def detect_outliers(
        self,
        divergence_threshold: float = 0.4,
        min_samples: int = 100
    ) -> List[Dict]:
        """
        Обнаружить outliers - пары где rule-based и semantic сильно расходятся

        Args:
            divergence_threshold: Порог расхождения (0-1)
            min_samples: Минимальное количество пар для анализа

        Returns:
            Список outliers с информацией о расхождении
        """
        outliers = []

        # Получить размеченные данные
        X, y = self.collector.get_labeled_data()

        if len(X) < min_samples:
            logger.warning(f"Недостаточно данных: {len(X)} < {min_samples}")
            return outliers

        logger.info(f"Анализ {len(X)} пар на outliers...")

        for i, features in enumerate(X):
            text1 = features.get('text1', '')
            text2 = features.get('text2', '')
            category1 = features.get('category1', '')
            category2 = features.get('category2', '')

            if not text1 or not text2:
                continue

            # Rule-based score
            rule_result = self.matcher.compute_enhanced_score(
                text1, text2, category1, category2
            )
            rule_score = rule_result['total_score']

            # Semantic score
            semantic_score = self.embedder.similarity(text1, text2)

            # Расхождение
            divergence = abs(rule_score - semantic_score)

            if divergence >= divergence_threshold:
                outlier = {
                    'pair_id': f"pair_{i}",
                    'text1': text1,
                    'text2': text2,
                    'category1': category1,
                    'category2': category2,
                    'rule_score': rule_score,
                    'semantic_score': semantic_score,
                    'divergence': divergence,
                    'is_match': y[i],
                    'timestamp': datetime.now().isoformat(),
                }
                outliers.append(outlier)

        logger.info(f"Найдено {len(outliers)} outliers с divergence >= {divergence_threshold}")

        # Сохранить outliers
        if outliers:
            outliers_file = self.output_dir / f"outliers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(outliers_file, 'w', encoding='utf-8') as f:
                json.dump(outliers, f, indent=2, ensure_ascii=False)
            logger.info(f"Outliers сохранены: {outliers_file}")

        return outliers

    def validate_semantic_consistency(
        self,
        test_pairs: Optional[List[Tuple[str, str, str, str, bool]]] = None
    ) -> Dict[str, float]:
        """
        Валидировать consistency semantic matching

        Args:
            test_pairs: Список тестовых пар (text1, text2, cat1, cat2, expected_match)
                       Если None, используется внутренний тестовый набор

        Returns:
            Метрики consistency
        """
        if test_pairs is None:
            # Внутренний тестовый набор для проверки consistency
            test_pairs = [
                # Совпадающие пары (должны иметь высокий score)
                ("велосипед горный", "велосипед горный", "спорт", "спорт", True),
                ("айфон 13", "айфон 13", "электроника", "электроника", True),
                ("пуховик зимний", "куртка зимняя", "одежда", "одежда", True),

                # Частично совпадающие (средний score)
                ("велосипед горный", "велосипед городской", "спорт", "спорт", True),
                ("айфон", "чехол для айфона", "электроника", "электроника", False),

                # Не совпадающие (низкий score)
                ("велосипед", "диван", "спорт", "мебель", False),
                ("книга", "велосипед", "книги", "спорт", False),
            ]

        results = {
            'total_pairs': len(test_pairs),
            'correct_predictions': 0,
            'consistency_score': 0.0,
            'semantic_vs_rule_agreement': 0.0,
        }

        semantic_scores = []
        rule_scores = []
        agreements = []

        for text1, text2, cat1, cat2, expected_match in test_pairs:
            # Semantic score
            semantic_score = self.embedder.similarity(text1, text2)

            # Rule-based score
            rule_result = self.matcher.compute_enhanced_score(text1, text2, cat1, cat2)
            rule_score = rule_result['total_score']

            # Hybrid score (если ML доступна)
            if self.predictor.is_available():
                features = {
                    'text1': text1, 'text2': text2,
                    'category1': cat1, 'category2': cat2
                }
                features.update({
                    'equivalence_score': rule_result['base_score'],
                    'language_similarity': 0.5,
                    'category_match': rule_result.get('category_weight', 1.0),
                    'synonym_ratio': 0.5,
                    'word_order_penalty': 0.0,
                    'contextual_bonus': rule_result.get('contextual_bonus', 0.0),
                })

                try:
                    ml_score = self.predictor.predict(features, return_proba=True)
                    hybrid_score = (rule_score + ml_score + semantic_score) / 3
                except Exception:
                    hybrid_score = (rule_score + semantic_score) / 2
            else:
                hybrid_score = (rule_score + semantic_score) / 2

            # Предсказание
            predicted_match = hybrid_score >= 0.5

            # Оценка consistency
            semantic_scores.append(semantic_score)
            rule_scores.append(rule_score)

            # Agreement между semantic и rule-based
            agreement = 1.0 - abs(semantic_score - rule_score)
            agreements.append(agreement)

            # Корректность предсказания
            if predicted_match == expected_match:
                results['correct_predictions'] += 1

        # Метрики
        results['consistency_score'] = results['correct_predictions'] / results['total_pairs']
        results['semantic_vs_rule_agreement'] = np.mean(agreements)
        results['semantic_score_mean'] = np.mean(semantic_scores)
        results['rule_score_mean'] = np.mean(rule_scores)

        logger.info("Semantic consistency validation:")
        logger.info(f"  Consistency: {results['consistency_score']:.3f}")
        logger.info(f"  Semantic-Rule agreement: {results['semantic_vs_rule_agreement']:.3f}")

        return results

    def generate_comprehensive_report(self) -> Dict:
        """
        Генерировать комплексный отчёт о semantic matching

        Returns:
            Полный отчёт со всеми метриками
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'semantic_embedder_available': self.embedder.is_available(),
            'ml_model_available': self.predictor.is_available(),
        }

        # Статистика данных
        data_stats = self.collector.get_statistics()
        report['data_stats'] = data_stats

        # Outliers
        outliers = self.detect_outliers()
        report['outliers_count'] = len(outliers)
        report['outliers_sample'] = outliers[:5] if outliers else []

        # Consistency validation
        consistency = self.validate_semantic_consistency()
        report['consistency_metrics'] = consistency

        # Semantic-Rule divergence analysis
        if data_stats['labeled_pairs'] > 0:
            divergences = []
            X, y = self.collector.get_labeled_data()

            for features in X[:min(100, len(X))]:  # Анализируем первые 100 пар
                text1 = features.get('text1', '')
                text2 = features.get('text2', '')
                cat1 = features.get('category1', '')
                cat2 = features.get('category2', '')

                if text1 and text2:
                    rule_result = self.matcher.compute_enhanced_score(text1, text2, cat1, cat2)
                    semantic_score = self.embedder.similarity(text1, text2)
                    divergence = abs(rule_result['total_score'] - semantic_score)
                    divergences.append(divergence)

            if divergences:
                report['divergence_analysis'] = {
                    'mean_divergence': np.mean(divergences),
                    'max_divergence': np.max(divergences),
                    'divergence_std': np.std(divergences),
                    'high_divergence_pairs': sum(1 for d in divergences if d > 0.3),
                }

        # Сохранить отчёт
        report_file = self.output_dir / f"semantic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Комплексный отчёт сохранён: {report_file}")

        return report

    def export_training_candidates(self, min_divergence: float = 0.4) -> List[Dict]:
        """
        Экспортировать candidates для дополнительного обучения

        Args:
            min_divergence: Минимальное расхождение для экспорта

        Returns:
            Список пар для ручной разметки
        """
        candidates = []

        # Найти пары с высоким расхождением
        outliers = self.detect_outliers(divergence_threshold=min_divergence)

        for outlier in outliers[:50]:  # Ограничить до 50 кандидатов
            candidate = {
                'text1': outlier['text1'],
                'text2': outlier['text2'],
                'category1': outlier['category1'],
                'category2': outlier['category2'],
                'rule_score': outlier['rule_score'],
                'semantic_score': outlier['semantic_score'],
                'divergence': outlier['divergence'],
                'needs_manual_labeling': True,
            }
            candidates.append(candidate)

        # Сохранить candidates
        if candidates:
            candidates_file = self.output_dir / f"training_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(candidates_file, 'w', encoding='utf-8') as f:
                json.dump(candidates, f, indent=2, ensure_ascii=False)
            logger.info(f"Training candidates сохранены: {candidates_file}")

        return candidates


def run_semantic_diagnostics_cli():
    """CLI функция для запуска диагностики"""
    import argparse

    parser = argparse.ArgumentParser(description="Semantic Diagnostics для FreeMarket")
    parser.add_argument("--outliers", action="store_true", help="Найти outliers")
    parser.add_argument("--consistency", action="store_true", help="Проверить consistency")
    parser.add_argument("--report", action="store_true", help="Генерировать полный отчёт")
    parser.add_argument("--candidates", action="store_true", help="Экспортировать training candidates")
    parser.add_argument("--output-dir", default="backend/monitoring/reports", help="Директория для отчётов")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    diagnostics = SemanticDiagnostics(output_dir=args.output_dir)

    if args.outliers:
        outliers = diagnostics.detect_outliers()
        print(f"Найдено outliers: {len(outliers)}")

    if args.consistency:
        consistency = diagnostics.validate_semantic_consistency()
        print(f"Consistency score: {consistency['consistency_score']:.3f}")

    if args.report:
        report = diagnostics.generate_comprehensive_report()
        print(f"Отчёт сгенерирован: {len(report)} метрик")

    if args.candidates:
        candidates = diagnostics.export_training_candidates()
        print(f"Training candidates: {len(candidates)}")

    if not any([args.outliers, args.consistency, args.report, args.candidates]):
        print("Используйте --help для списка команд")
        print("Пример: python -m backend.monitoring.semantic_diagnostics --report")


if __name__ == "__main__":
    run_semantic_diagnostics_cli()

