"""
Обучение ML-модели для matching
Этап 2: Адаптивное обучение весов
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import pickle

try:
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import (
        precision_score, recall_score, f1_score,
        roc_auc_score, confusion_matrix, classification_report
    )
    try:
        import lightgbm as lgb
        LIGHTGBM_AVAILABLE = True
    except ImportError:
        LIGHTGBM_AVAILABLE = False
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not installed. Install with: pip install scikit-learn")

from backend.matching.features_extractor import TrainingDataCollector
from backend.matching.semantic_embedder import SemanticFeatureCalculator, get_embedder

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Обучение модели для предсказания совпадений"""

    def __init__(
        self,
        model_type: str = "logistic",
        model_dir: str = "backend/data/models"
    ):
        """
        Инициализация тренера

        Args:
            model_type: "logistic" или "lightgbm"
            model_dir: Директория для сохранения моделей
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn не установлен. Установите: pip install scikit-learn")

        self.model_type = model_type
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.model = None
        self.scaler = StandardScaler()
        self.threshold = 0.5  # Базовый порог
        self.semantic_calculator = SemanticFeatureCalculator()

        logger.info(f"ModelTrainer инициализирован: model_type={model_type}")
        if self.semantic_calculator.embedder.is_available():
            logger.info("✓ Semantic embedder доступен")
        else:
            logger.warning("⚠ Semantic embedder недоступен, semantic features отключены")

    def load_training_data(
        self,
        collector: TrainingDataCollector,
        min_samples: int = 50
    ) -> Tuple[List[Dict], List[int]]:
        """
        Загрузить размеченные данные для обучения

        Args:
            collector: TrainingDataCollector с данными
            min_samples: Минимальное количество примеров

        Returns:
            (X, y) где X - признаки, y - метки
        """
        X, y = collector.get_labeled_data()

        if len(X) < min_samples:
            raise ValueError(
                f"Недостаточно данных для обучения: {len(X)} < {min_samples}. "
                f"Необходимо собрать больше размеченных пар."
            )

        positive = sum(y)
        negative = len(y) - positive
        pos_ratio = positive / len(y) if len(y) > 0 else 0

        logger.info(f"Загружено данных для обучения:")
        logger.info(f"  Всего: {len(X)}")
        logger.info(f"  Положительных: {positive} ({pos_ratio*100:.1f}%)")
        logger.info(f"  Отрицательных: {negative} ({(1-pos_ratio)*100:.1f}%)")

        # Проверка баланса данных
        if not (0.3 <= pos_ratio <= 0.7):
            raise ValueError(
                f"Dataset imbalance detected: positive ratio = {pos_ratio:.2f}. "
                f"Требуется баланс 30-70% положительных примеров. "
                f"Текущее распределение: {positive} положительных, {negative} отрицательных."
            )

        return X, y

    def prepare_features(
        self,
        X: List[Dict],
        add_category_features: bool = True
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Подготовить признаки для обучения

        Args:
            X: Список словарей с признаками
            add_category_features: Добавить one-hot encoding категорий

        Returns:
            (Массив признаков, список имён признаков)
        """
        base_feature_names = [
            'equivalence_score',
            'language_similarity',
            'category_match',
            'synonym_ratio',
            'word_order_penalty',
            'contextual_bonus',
            'word_overlap',
            'text_length_diff',
        ]

        # Преобразовать в DataFrame
        df = pd.DataFrame(X)

        # Проверить наличие всех признаков
        missing = set(base_feature_names) - set(df.columns)
        if missing:
            logger.warning(f"Отсутствуют признаки: {missing}. Заполняю нулями.")
            for col in missing:
                df[col] = 0.0

        # Базовые признаки
        feature_df = df[base_feature_names].copy()
        feature_names = base_feature_names.copy()

        # Добавить категорийные фичи (one-hot encoding)
        if add_category_features and 'category1' in df.columns and 'category2' in df.columns:
            # Определить уникальные категории
            all_categories = set(df['category1'].unique()) | set(df['category2'].unique())
            category_list = sorted(list(all_categories))

            # One-hot для category1 и category2
            for cat in category_list:
                feature_df[f'cat1_{cat}'] = (df['category1'] == cat).astype(int)
                feature_df[f'cat2_{cat}'] = (df['category2'] == cat).astype(int)
                feature_names.extend([f'cat1_{cat}', f'cat2_{cat}'])

            logger.info(f"Добавлено {len(category_list) * 2} категорийных фич: {category_list}")

        # Добавить семантические признаки
        if add_category_features:
            # Добавляем semantic features для каждой пары
            semantic_features = []
            for _, row in df.iterrows():
                text1 = row.get('text1', '')
                text2 = row.get('text2', '')

                # Добавляем semantic признаки
                semantic_row = self.semantic_calculator.add_semantic_features(
                    {}, text1, text2
                )
                semantic_features.append(semantic_row)

            # Конвертируем в DataFrame и добавляем
            semantic_df = pd.DataFrame(semantic_features)
            feature_df = pd.concat([feature_df, semantic_df], axis=1)
            feature_names.extend(semantic_df.columns.tolist())

            logger.info(f"Добавлены семантические фичи: {semantic_df.columns.tolist()}")

        X_array = feature_df.values

        return X_array, feature_names

    def train(
        self,
        collector: TrainingDataCollector,
        test_size: float = 0.2,
        min_samples: int = 50
    ) -> Dict[str, float]:
        """
        Обучить модель

        Args:
            collector: TrainingDataCollector с данными
            test_size: Доля тестовой выборки
            min_samples: Минимальное количество примеров

        Returns:
            Словарь с метриками
        """
        # Загрузить данные
        X_raw, y = self.load_training_data(collector, min_samples)

        # Подготовить признаки
        X, feature_names = self.prepare_features(X_raw, add_category_features=True)
        y = np.array(y)

        # Сохранить список признаков
        self.feature_names = feature_names

        # Разделить на train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        logger.info(f"Разделение данных: train={len(X_train)}, test={len(X_test)}")

        # Масштабирование
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Обучение модели
        if self.model_type == "logistic":
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                class_weight='balanced'  # Балансировка классов
            )
        elif self.model_type == "lightgbm" and LIGHTGBM_AVAILABLE:
            self.model = lgb.LGBMClassifier(
                random_state=42,
                class_weight='balanced',
                n_estimators=100,
                learning_rate=0.1
            )
        else:
            raise ValueError(f"Неизвестный тип модели: {self.model_type}")

        logger.info(f"Обучение модели {self.model_type}...")
        self.model.fit(X_train_scaled, y_train)

        # Предсказания на тестовой выборке
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

        # Метрики
        metrics = {
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'accuracy': (y_test == y_pred).mean(),
        }

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        metrics['true_negatives'] = int(cm[0, 0])
        metrics['false_positives'] = int(cm[0, 1])
        metrics['false_negatives'] = int(cm[1, 0])
        metrics['true_positives'] = int(cm[1, 1])

        logger.info("Метрики на тестовой выборке:")
        for key, value in metrics.items():
            if key != 'confusion_matrix':
                logger.info(f"  {key}: {value:.4f}")

        # Classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        logger.info("\nClassification Report:")
        logger.info(f"  Precision (0): {report['0']['precision']:.4f}")
        logger.info(f"  Precision (1): {report['1']['precision']:.4f}")
        logger.info(f"  Recall (0): {report['0']['recall']:.4f}")
        logger.info(f"  Recall (1): {report['1']['recall']:.4f}")

        return metrics

    def save_model(self, metadata: Optional[Dict] = None):
        """Сохранить модель и метаданные"""
        if self.model is None:
            raise ValueError("Модель не обучена. Вызовите train() сначала.")

        model_path = self.model_dir / "matching_model.pkl"
        scaler_path = self.model_dir / "scaler.pkl"
        metadata_path = self.model_dir / "model_metadata.json"

        # Сохранить модель
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Модель сохранена: {model_path}")

        # Сохранить scaler
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        logger.info(f"Scaler сохранён: {scaler_path}")

        # Сохранить метаданные
        model_metadata = {
            'model_type': self.model_type,
            'threshold': self.threshold,
            'feature_count': len(self.feature_names) if hasattr(self, 'feature_names') else 8,
            'feature_names': getattr(self, 'feature_names', []),
            'saved_at': str(pd.Timestamp.now()),
        }

        if metadata:
            model_metadata.update(metadata)

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(model_metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Метаданные сохранены: {metadata_path}")

        # Сохранить список признаков отдельно
        feature_columns_path = self.model_dir / "feature_columns.json"
        with open(feature_columns_path, 'w', encoding='utf-8') as f:
            json.dump(getattr(self, 'feature_names', []), f, indent=2, ensure_ascii=False)
        logger.info(f"Список признаков сохранён: {feature_columns_path}")

    def load_model(self) -> bool:
        """Загрузить сохранённую модель"""
        model_path = self.model_dir / "matching_model.pkl"
        scaler_path = self.model_dir / "scaler.pkl"
        metadata_path = self.model_dir / "model_metadata.json"

        if not model_path.exists():
            logger.warning(f"Модель не найдена: {model_path}")
            return False

        # Загрузить модель
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info(f"Модель загружена: {model_path}")

        # Загрузить scaler
        if scaler_path.exists():
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info(f"Scaler загружен: {scaler_path}")

        # Загрузить метаданные
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                self.threshold = metadata.get('threshold', 0.5)
                logger.info(f"Метаданные загружены: threshold={self.threshold}")

        return True


def train_matching_model(
    collector: TrainingDataCollector,
    model_type: str = "logistic",
    test_size: float = 0.2,
    min_samples: int = 50
) -> Dict[str, float]:
    """
    Обучение модели matching

    Args:
        collector: TrainingDataCollector с данными
        model_type: "logistic" или "lightgbm"
        test_size: Доля тестовой выборки
        min_samples: Минимальное количество примеров

    Returns:
        Словарь с метриками
    """
    trainer = ModelTrainer(model_type=model_type)
    metrics = trainer.train(collector, test_size=test_size, min_samples=min_samples)
    trainer.save_model(metadata={'metrics': metrics})

    return metrics


if __name__ == "__main__":
    # Пример использования
    logging.basicConfig(level=logging.INFO)

    collector = TrainingDataCollector()

    # Проверить статистику
    stats = collector.get_statistics()
    print(f"\nСтатистика данных:")
    print(f"  Всего пар: {stats['total_pairs']}")
    print(f"  Размеченных: {stats['labeled_pairs']}")
    print(f"  Положительных: {stats['matches']}")
    print(f"  Отрицательных: {stats['non_matches']}")

    if stats['labeled_pairs'] >= 50:
        print("\nОбучение модели...")
        metrics = train_matching_model(collector, model_type="logistic")
        print(f"\nМетрики: {metrics}")
    else:
        print(f"\nНедостаточно данных для обучения: {stats['labeled_pairs']} < 50")
        print("Соберите больше размеченных пар через TrainingDataCollector.")

