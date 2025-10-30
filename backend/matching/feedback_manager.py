"""
Управление обратной связью пользователей
Этап 2: Feedback loop для непрерывного улучшения
"""

import json
import logging
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

from backend.matching.features_extractor import TrainingDataCollector, MatchingFeatures

logger = logging.getLogger(__name__)


class FeedbackManager:
    """Управление пользовательской обратной связью"""

    def __init__(
        self,
        collector: Optional[TrainingDataCollector] = None,
        feedback_file: str = "backend/data/feedback_log.jsonl"
    ):
        """
        Инициализация менеджера обратной связи

        Args:
            collector: TrainingDataCollector для сохранения данных
            feedback_file: Путь к файлу логов обратной связи
        """
        self.collector = collector or TrainingDataCollector()
        self.feedback_file = Path(feedback_file)
        self.feedback_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"FeedbackManager инициализирован: {feedback_file}")

    def log_feedback(
        self,
        pair_id: str,
        user_id: str,
        is_match: bool,
        prediction_score: float,
        user_action: str = "confirmed",
        metadata: Optional[Dict] = None
    ):
        """
        Записать обратную связь пользователя

        Args:
            pair_id: ID пары
            user_id: ID пользователя
            is_match: Реальное совпадение (True/False)
            prediction_score: Предсказанный score модели
            user_action: Действие пользователя ("confirmed", "rejected", "ignored")
            metadata: Дополнительные метаданные
        """
        feedback_entry = {
            'pair_id': pair_id,
            'user_id': user_id,
            'is_match': is_match,
            'prediction_score': prediction_score,
            'user_action': user_action,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
        }

        # Сохранить в лог
        with open(self.feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_entry, ensure_ascii=False) + '\n')

        # Добавить в TrainingDataCollector
        self.collector.add_user_feedback(pair_id, is_match)

        logger.info(f"Обратная связь записана: pair_id={pair_id}, is_match={is_match}")

    def log_matching_result(
        self,
        pair_id: str,
        features: MatchingFeatures,
        prediction_score: float,
        was_shown: bool = True
    ):
        """
        Записать результат matching для последующего анализа

        Args:
            pair_id: ID пары
            features: Признаки пары
            prediction_score: Предсказанный score
            was_shown: Был ли результат показан пользователю
        """
        # Добавить пару в коллектор
        features.pair_id = pair_id
        self.collector.add_pair(features, save_immediately=True)

        # Записать метаданные
        if was_shown:
            metadata = {
                'prediction_score': prediction_score,
                'shown_to_user': True,
            }

            entry = {
                'pair_id': pair_id,
                'prediction_score': prediction_score,
                'shown_to_user': True,
                'timestamp': datetime.now().isoformat(),
            }

            with open(self.feedback_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def get_feedback_stats(self, days: int = 30) -> Dict:
        """
        Получить статистику обратной связи за период

        Args:
            days: Количество дней для анализа

        Returns:
            Словарь со статистикой
        """
        if not self.feedback_file.exists():
            return {
                'total_feedback': 0,
                'confirmed_matches': 0,
                'rejected_matches': 0,
                'accuracy': 0.0,
            }

        confirmed = 0
        rejected = 0
        total = 0

        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)
                    timestamp = datetime.fromisoformat(entry['timestamp']).timestamp()

                    if timestamp < cutoff_date:
                        continue

                    total += 1
                    if entry.get('user_action') == 'confirmed':
                        confirmed += 1
                    elif entry.get('user_action') == 'rejected':
                        rejected += 1
                except Exception as e:
                    logger.warning(f"Ошибка при чтении записи обратной связи: {e}")

        accuracy = confirmed / total if total > 0 else 0.0

        return {
            'total_feedback': total,
            'confirmed_matches': confirmed,
            'rejected_matches': rejected,
            'accuracy': accuracy,
            'period_days': days,
        }

    def commit_to_training(self) -> int:
        """
        Коммит данных из feedback в TrainingDataCollector

        Returns:
            Количество добавленных пар
        """
        if not self.feedback_file.exists():
            return 0

        added_count = 0

        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)
                    pair_id = entry.get('pair_id')
                    is_match = entry.get('is_match')

                    if pair_id and is_match is not None:
                        # Добавить обратную связь
                        self.collector.add_user_feedback(pair_id, is_match)
                        added_count += 1
                except Exception as e:
                    logger.warning(f"Ошибка при коммите обратной связи: {e}")

        logger.info(f"Добавлено {added_count} пар из feedback в training data")
        return added_count

    def calculate_runtime_metrics(self) -> Dict:
        """
        Вычислить runtime метрики на основе feedback

        Returns:
            Словарь с метриками precision/recall по feedback
        """
        if not self.feedback_file.exists():
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'total_feedback': 0,
            }

        true_positives = 0
        false_positives = 0
        false_negatives = 0
        total = 0

        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)
                    if 'is_match' not in entry or 'prediction_score' not in entry:
                        continue

                    is_match = entry['is_match']
                    prediction_score = entry['prediction_score']
                    user_action = entry.get('user_action', 'unknown')

                    # Используем threshold 0.5 для бинарного предсказания
                    predicted_match = prediction_score >= 0.5

                    if user_action == 'confirmed' and is_match:
                        true_positives += 1
                    elif user_action == 'rejected' and predicted_match:
                        false_positives += 1
                    elif user_action == 'confirmed' and not is_match:
                        false_negatives += 1

                    total += 1
                except Exception as e:
                    logger.warning(f"Ошибка при вычислении метрик: {e}")

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'total_feedback': total,
        }

    def save_metrics_report(self, output_path: Optional[str] = None):
        """
        Сохранить отчёт с метриками в JSON

        Args:
            output_path: Путь для сохранения (по умолчанию feedback_stats.json)
        """
        if output_path is None:
            output_path = self.feedback_file.parent / "feedback_stats.json"

        stats = self.get_feedback_stats(days=30)
        runtime_metrics = self.calculate_runtime_metrics()

        report = {
            'feedback_stats': stats,
            'runtime_metrics': runtime_metrics,
            'generated_at': datetime.now().isoformat(),
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Отчёт метрик сохранён: {output_path}")

    def commit_to_training(self, auto_retrain: bool = False, min_new_feedback: int = 50) -> Dict[str, int]:
        """
        Коммит данных из feedback в TrainingDataCollector с опцией авто-переобучения

        Args:
            auto_retrain: Автоматически запустить переобучение если данных достаточно
            min_new_feedback: Минимальное количество новой обратной связи

        Returns:
            Словарь с результатами коммита
        """
        result = {
            'committed_pairs': 0,
            'retrained': False,
            'new_model_version': None,
        }

        # Коммит данных
        result['committed_pairs'] = self.commit_to_training_data()

        if auto_retrain and self.should_retrain(min_new_feedback):
            logger.info("Запуск автоматического переобучения...")
            try:
                from backend.matching.train_model import train_matching_model
                metrics = train_matching_model(self.collector)
                result['retrained'] = True
                result['new_model_version'] = f"v{int(datetime.now().timestamp())}"
                result['metrics'] = metrics

                logger.info(f"Модель успешно переобучена: {result['new_model_version']}")
            except Exception as e:
                logger.error(f"Ошибка при переобучении: {e}")
                result['retrain_error'] = str(e)

        return result

    def commit_to_training_data(self) -> int:
        """
        Коммит только данных (без переобучения)

        Returns:
            Количество добавленных пар
        """
        if not self.feedback_file.exists():
            return 0

        added_count = 0

        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)
                    pair_id = entry.get('pair_id')
                    is_match = entry.get('is_match')

                    if pair_id and is_match is not None:
                        # Добавить обратную связь
                        self.collector.add_user_feedback(pair_id, is_match)
                        added_count += 1
                except Exception as e:
                    logger.warning(f"Ошибка при коммите обратной связи: {e}")

        logger.info(f"Добавлено {added_count} пар из feedback в training data")
        return added_count

    def should_retrain(self, min_new_feedback: int = 50) -> bool:
        """
        Проверить, нужно ли переобучать модель

        Args:
            min_new_feedback: Минимальное количество новой обратной связи

        Returns:
            True если нужно переобучить
        """
        stats = self.get_feedback_stats(days=7)  # За последнюю неделю

        # Проверить количество неразмеченных пар
        collector_stats = self.collector.get_statistics()
        unlabeled = collector_stats['total_pairs'] - collector_stats['labeled_pairs']

        return (
            stats['total_feedback'] >= min_new_feedback or
            unlabeled >= min_new_feedback
        )

    def get_model_versions_history(self, models_dir: str = "backend/data/models") -> List[Dict]:
        """
        Получить историю версий модели

        Args:
            models_dir: Директория с моделями

        Returns:
            Список версий модели с метриками
        """
        from pathlib import Path
        models_path = Path(models_dir)

        versions = []
        if models_path.exists():
            for metadata_file in models_path.glob("model_metadata_v*.json"):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        versions.append(metadata)
                except Exception as e:
                    logger.warning(f"Ошибка чтения метаданных {metadata_file}: {e}")

        # Сортировать по дате
        versions.sort(key=lambda x: x.get('saved_at', ''), reverse=True)
        return versions


if __name__ == "__main__":
    # Пример использования
    logging.basicConfig(level=logging.INFO)

    manager = FeedbackManager()

    # Логирование обратной связи
    manager.log_feedback(
        pair_id="pair_001",
        user_id="user_123",
        is_match=True,
        prediction_score=0.85,
        user_action="confirmed"
    )

    # Статистика
    stats = manager.get_feedback_stats(days=7)
    print(f"\nСтатистика обратной связи (7 дней):")
    print(f"  Всего: {stats['total_feedback']}")
    print(f"  Подтверждено: {stats['confirmed_matches']}")
    print(f"  Отклонено: {stats['rejected_matches']}")
    print(f"  Точность: {stats['accuracy']:.2%}")

    # Проверка необходимости переобучения
    if manager.should_retrain():
        print("\n⚠ Рекомендуется переобучить модель")
    else:
        print("\n✓ Достаточно данных для переобучения")

