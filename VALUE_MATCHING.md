# FreeMarket API - Value Range Matching

## Новые возможности: Диапазоны ценностей и оптимальный матчинг

### Расширение модели данных

Объявления теперь поддерживают диапазоны ценностей для более точного матчинга:

```json
{
  "user_id": 1,
  "kind": 1,
  "category": "electronics",
  "title": "Laptop",
  "description": "Gaming laptop",
  "wants": ["phone"],
  "offers": ["laptop"],
  "value_min": 500,
  "value_max": 1000,
  "lease_term": "P1M",  // ISO 8601 duration
  "is_money": false
}
```

### Оптимальный матчинг

#### Алгоритм скоринга
```
score = α * text_similarity + β * tag_similarity + γ * value_overlap + δ * trust_score
```

- `text_similarity`: Косинусное сходство эмбеддингов Sentence-BERT
- `tag_similarity`: Пересечение wants/offers тегов
- `value_overlap`: Пересечение диапазонов ценностей
- `trust_score`: Доверие пользователя с учетом decay

#### Многоуровневый поиск
Система возвращает оптимальное количество результатов:
1. **Высокая уверенность** (score ≥ 0.8): до 10 результатов
2. **Средняя уверенность** (score ≥ 0.6): до 20 результатов
3. **Расширенный поиск** (score ≥ 0.4): до 30 результатов

### API

#### Получение оптимальных матчей
```
GET /matches/{item_id}/optimal
```

Возвращает:
```json
[
  {
    "item_a": 1,
    "item_b": 2,
    "score": 0.85,
    "reason": "high_confidence",
    "reasons": {
      "text_similarity": 0.9,
      "tag_similarity": 0.8,
      "value_overlap": 0.7,
      "category_weights": {"text": 0.5, "attributes": 0.5}
    },
    "status": "new"
  }
]
```

### A/B тестирование

Пользователи автоматически распределяются по группам с разными порогами матчинга:
- **Control**: score ≥ 0.5, top_k = 5
- **Variant A**: score ≥ 0.6, top_k = 3 (строже)
- **Variant B**: score ≥ 0.4, top_k = 7 (мягче)

### Графовые обмены

Для многосторонних обменов используется NetworkX для поиска циклов в графе потенциальных сделок.

### Установка зависимостей

```bash
pip install -r requirements.txt
```

Новые пакеты:
- `sentence-transformers`: Для эмбеддингов текста
- `lightgbm`: Для learn-to-rank
- `networkx`: Для графовых алгоритмов
- `redis`: Для очередей и кеширования

### Автоматический поток при создании анкеты

1. **Пользователь создаёт анкету** (`POST /items/`)
2. **FastAPI сохраняет** анкету в БД и ставит задачу в Redis-очередь
3. **Фоновый воркер** обрабатывает задачу:
   - Находит все подходящие активные анкеты
   - Считает score для каждой пары
   - Проверяет взаимность (существующие матчи)
   - Создаёт новые матчи или обновляет статус на "matched"
4. **Уведомления** рассылаются обоим пользователям при взаимном совпадении

### Таблица взаимных матчей

```sql
CREATE TABLE mutual_matches (
  id BIGSERIAL PRIMARY KEY,
  item_a BIGINT REFERENCES items(id),
  item_b BIGINT REFERENCES items(id),
  matched_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE (LEAST(item_a, item_b), GREATEST(item_a, item_b))
);
```

### Запуск воркера

```bash
python worker.py
```

Воркер будет автоматически обрабатывать задачи из Redis-очереди.
