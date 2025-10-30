# 🚀 Этап 2.1-2.3: Road to Production

## 📋 Исправленные слабые места

### ✅ 1. Проверка баланса данных

**Исправлено в:** `backend/matching/train_model.py`

```python
# Проверка баланса данных
if not (0.3 <= pos_ratio <= 0.7):
    raise ValueError(
        f"Dataset imbalance detected: positive ratio = {pos_ratio:.2f}. "
        f"Требуется баланс 30-70% положительных примеров."
    )
```

**Результат:** Автоматическая валидация баланса перед обучением

---

### ✅ 2. Категорийные фичи (one-hot encoding)

**Исправлено в:** `backend/matching/train_model.py`

```python
# Добавить категорийные фичи (one-hot encoding)
if add_category_features and 'category1' in df.columns and 'category2' in df.columns:
    for cat in category_list:
        feature_df[f'cat1_{cat}'] = (df['category1'] == cat).astype(int)
        feature_df[f'cat2_{cat}'] = (df['category2'] == cat).astype(int)
```

**Результат:** Модель учитывает категории напрямую (cat1_электроника, cat2_мебель, etc.)

---

### ✅ 3. Нормализация комбинации scores

**Исправлено в:** `backend/matching/model_predictor.py`

```python
def combine_scores(rule_based_score, ml_score, ml_weight=0.4, normalize=True):
    if normalize:
        # Нормализованная комбинация: (α * rb + β * ml) / (α + β)
        combined = (rule_based_score * rule_weight + ml_score * ml_weight) / (rule_weight + ml_weight)
    return min(max(combined, 0.0), 1.0)
```

**Результат:** Score всегда в диапазоне [0, 1], нет перескоков

---

### ✅ 4. Замкнутый feedback loop

**Исправлено в:** `backend/matching/feedback_manager.py`

```python
def commit_to_training(self) -> int:
    """Коммит данных из feedback в TrainingDataCollector"""
    # Переносит все feedback записи в training_pairs.jsonl
```

**Результат:** Автоматический перенос feedback → training data

---

### ✅ 5. Мониторинг метрик

**Исправлено в:** `backend/matching/feedback_manager.py`

```python
def calculate_runtime_metrics(self) -> Dict:
    """Вычислить runtime метрики на основе feedback"""
    # Precision, Recall, F1-score по реальным пользовательским действиям

def save_metrics_report(self, output_path):
    """Сохранить отчёт с метриками в JSON"""
    # feedback_stats.json с полной статистикой
```

**Результат:** Постоянный контроль качества на проде

---

### ✅ 6. Singleton для ModelPredictor

**Исправлено в:** `backend/matching/model_predictor.py`

```python
class ModelPredictor:
    _instance = None

    def __new__(cls, model_dir="backend/data/models"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**Результат:** Модель загружается один раз, переиспользуется

---

## 📋 План Этапа 2.1-2.3

### Этап 2.1 — Data Phase (Сбор и очистка данных)

**Цель:** Подготовить 100-200 качественных пар

**Действия:**

1. **Интеграция TrainingDataCollector в API**
   ```python
   # backend/api/endpoints/listings_exchange.py
   from backend.matching.features_extractor import TrainingDataCollector, FeatureCalculator

   collector = TrainingDataCollector()

   # После matching:
   features = FeatureCalculator.create_training_features(...)
   collector.add_pair(features)
   ```

2. **Автоматическая валидация баланса**
   - ✅ Уже реализовано в `train_model.py`
   - Проверка: `assert 0.3 < pos_ratio < 0.7`

3. **Валидация разнообразия категорий**
   ```python
   # Проверка распределения по категориям
   category_distribution = df['category1'].value_counts()
   assert len(category_distribution) >= 4, "Недостаточно разнообразия категорий"
   ```

**Критерии готовности:**
- ✅ ≥ 100 пар в `training_pairs.jsonl`
- ✅ Баланс 30-70% положительных
- ✅ Минимум 4 категории представлены

---

### Этап 2.2 — Training Phase (Автообучение модели)

**Цель:** Устойчивый ML-score без overfit

**Действия:**

1. **Обучение модели**
   ```bash
   python -m backend.matching.train_model
   ```

2. **Оценка метрик**
   - Precision > 0.80
   - Recall > 0.75
   - F1-score > 0.77

3. **Оптимизация threshold**
   ```python
   from backend.matching.threshold_tuner import ThresholdTuner

   tuner = ThresholdTuner(metric="f1")
   best_metrics = tuner.find_optimal_threshold(y_test, y_proba)
   ```

4. **Сохранение модели и метаданных**
   - ✅ `matching_model.pkl`
   - ✅ `scaler.pkl`
   - ✅ `feature_columns.json`
   - ✅ `model_metadata.json`

**Результат:**
- Модель обучена и сохранена
- Threshold оптимизирован
- Метрики записаны в метаданные

---

### Этап 2.3 — Feedback Phase (Замкнуть обратную связь)

**Цель:** Самообучение системы

**Действия:**

1. **Коммит feedback в training data**
   ```python
   from backend.matching.feedback_manager import FeedbackManager

   manager = FeedbackManager()
   added_count = manager.commit_to_training()
   ```

2. **Cron-задача для переобучения**
   ```bash
   # Crontab: раз в 30 дней
   0 2 1 * * cd /opt/freemarket && python -m backend.matching.train_model
   ```

3. **Проверка необходимости retrain**
   ```python
   if manager.should_retrain(min_new_feedback=50):
       train_matching_model(collector)
   ```

**Результат:**
- Feedback автоматически переносится в training data
- Переобучение запускается автоматически при накоплении данных

---

### Этап 2.4 — Semantic Prep (Подготовка к Этапу 3)

**Цель:** Плавный переход к семантике

**Действия:**

1. **Добавить semantic_similarity фичу**
   - Заглушка: всегда 0.0 (будет реализовано в Этапе 3)
   - Структура готова: `prepare_features()` проверяет наличие фичи

2. **Документация перехода**
   - `PHASE_3_SEMANTIC_PLAN.md` — план Этапа 3

**Результат:**
- Готовность к интеграции sentence embeddings

---

## 📊 Ожидаемые результаты

| Метрика | До Этапа 2 | После 2.1-2.3 | Улучшение |
|---------|-----------|---------------|-----------|
| **Precision** | 70% | **85-88%** | +15-18% |
| **Recall** | 70% | **82-85%** | +12-15% |
| **F1-score** | 70% # | **83-86%** | +13-16% |
| **Ложные совпадения** | 30% | **≤12%** | -60% |
| **Drift-контроль** | ❌ | ✅ | Стабильность |

---

## 🛠️ Технические дополнения

### ✅ Сохранение feature_columns.json

**Реализовано:** `train_model.py` сохраняет список признаков

```python
feature_columns_path = self.model_dir / "feature_columns.json"
with open(feature_columns_path, 'w') as f:
    json.dump(self.feature_names, f)
```

### ✅ Runtime метрики

**Реализовано:** `feedback_manager.py` вычисляет Precision/Recall

```python
metrics = manager.calculate_runtime_metrics()
# {'precision': 0.85, 'recall': 0.82, 'f1_score': 0.83, ...}
```

### ✅ Отчёт метрик

**Реализовано:** `feedback_manager.py` сохраняет отчёт

```python
manager.save_metrics_report()
# Сохраняет в backend/data/feedback_stats.json
```

---

## 📋 Чек-лист для production

- [ ] Набрано ≥ 100 размеченных пар
- [ ] Баланс данных 30-70% положительных
- [ ] Минимум 4 категории представлены
- [ ] Модель обучена (F1 > 0.77)
- [ ] Threshold оптимизирован
- [ ] Feedback loop интегрирован в API
- [ ] Cron-задача настроена для retrain
- [ ] Метрики собираются и логируются

---

## 🔄 Интеграция в production

### API Endpoint для feedback

```python
# backend/api/endpoints/matching.py
from backend.matching.feedback_manager import FeedbackManager

@router.post("/api/matching/feedback")
async def submit_feedback(
    pair_id: str,
    user_id: str,
    is_match: bool,
    prediction_score: float
):
    manager = FeedbackManager()
    manager.log_feedback(
        pair_id=pair_id,
        user_id=user_id,
        is_match=is_match,
        prediction_score=prediction_score,
        user_action="confirmed" if is_match else "rejected"
    )

    # Проверить необходимость retrain
    if manager.should_retrain():
        # Запустить retrain в фоне (Celery/Background task)
        retrain_model.delay()

    return {"status": "ok"}
```

---

## 📚 Документация

- 📖 `PHASE_2_PRODUCTION_READY_PLAN.md` — этот документ
- 📊 `PHASE_2_ML_IMPLEMENTATION_STATUS.md` — статус реализации
- 🔧 Код с улучшениями в каждом модуле

---

*Статус: 🟡 ГОТОВО К PRODUCTION*
*Последнее обновление: 2025-01-30*

